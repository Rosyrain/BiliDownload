"""
Bilibili video downloader core module.

This module provides the core functionality for downloading Bilibili videos including:
- Video information extraction
- Video and audio stream downloading
- FFmpeg-based media merging
- Series video handling
"""

import os
import re
import time
import subprocess
import requests
from typing import Dict
from .logger import get_logger
from src.core.config_manager import ConfigManager
import random


class BiliDownloader:
    """
    Core downloader for Bilibili videos.

    Handles video information extraction, downloading of video/audio streams,
    and merging using FFmpeg. Supports both single videos and series.
    """

    def __init__(self, config_manager=None):
        """
        Initialize the downloader.

        Args:
            config_manager: Optional configuration manager
        """
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Referer": "https://www.bilibili.com",
                "Origin": "https://www.bilibili.com",
            }
        )
        self.config_manager: ConfigManager = config_manager
        self.logger = get_logger(__name__)

    def get_video_info(self, url: str) -> Dict[str, any]:
        """
        Extract video information from Bilibili URL.

        Args:
            url (str): Bilibili video URL

        Returns:
            Dict[str, any]: Video information including title, duration, etc.
        """
        try:
            # Handle multi-part videos
            if "?p=" in url:
                url = url.split("?p=")[0]

            response = self.session.get(url)
            response.raise_for_status()

            # Extract video title
            title_match = re.search(r"<title[^>]*>([^<]+)</title>", response.text)
            title = title_match.group(1).strip() if title_match else "Unknown Title"

            # Extract playback information
            playinfo_match = re.search(
                r"window\.__playinfo__=({.*?})</script>", response.text
            )
            if playinfo_match:
                import json

                playinfo = json.loads(playinfo_match.group(1))
                return {"title": title, "playinfo": playinfo, "url": url}

            return {"title": title, "playinfo": None, "url": url}

        except Exception as e:
            self.logger.error(f"Failed to get video info from {url}: {e}")
            return {"title": "Error", "playinfo": None, "url": url}

    def download_video(
        self,
        url: str,
        save_path: str,
        ffmpeg_path: str = None,
        download_type: str = "full",
        final_path: str = None,
    ) -> bool:
        """
        Download a video from Bilibili.

        Args:
            url (str): URL of the video to download
            save_path (str): Path to save temporary files during download
            ffmpeg_path (str, optional): Path to FFmpeg executable
            download_type (str, optional): Type of download - "full" (video+audio), "audio" (audio only), "video" (video only)
            final_path (str, optional): Final path to save the output file (if different from save_path)

        Returns:
            bool: True if download successful, False otherwise
        """
        try:
            # If FFmpeg path not provided, get from config
            if not ffmpeg_path and self.config_manager:
                ffmpeg_path = self.config_manager.get_ffmpeg_path()

            # 如果未提供最终路径，使用save_path
            if not final_path:
                final_path = save_path

            # 确保最终保存目录存在
            import os

            final_dir = os.path.dirname(final_path)
            if not os.path.exists(final_dir):
                os.makedirs(final_dir, exist_ok=True)

            video_info = self.get_video_info(url)
            if not video_info["playinfo"]:
                self.logger.error("Failed to extract video information")
                # 记录标题获取失败
                try:
                    from src.core.logger import log_download_detail

                    log_download_detail("title", success=False, title="获取失败")
                except ImportError:
                    self.logger.error("无法导入log_download_detail函数")
                return False

            # 记录标题获取成功
            try:
                from src.core.logger import log_download_detail

                log_download_detail(
                    "title", success=True, title=video_info.get("title", "未知标题")
                )
            except ImportError:
                self.logger.error("无法导入log_download_detail函数")

            # Create temporary file paths
            video_temp = save_path + ".video.tmp"
            audio_temp = save_path + ".audio.tmp"

            success = True

            # Download based on type
            if download_type in ["full", "video"]:
                # Download video stream
                video_url = video_info["playinfo"]["data"]["dash"]["video"][0][
                    "baseUrl"
                ]
                self.logger.info(
                    f"视频URL: {video_url[:100]}..."
                )  # 只打印前100个字符，避免日志过长
                video_success = self._download_stream(video_url, video_temp)

                # 记录视频下载结果
                try:
                    from src.core.logger import log_download_detail

                    log_download_detail(
                        "video",
                        success=video_success,
                        url=video_url,
                        title=video_info.get("title", "未知标题"),
                    )
                except ImportError:
                    pass

                if not video_success:
                    self.logger.error("Failed to download video stream")
                    success = False

                # If video only, rename the temp file to final output
                if download_type == "video" and video_success:
                    final_video_path = final_path + ".mp4"
                    os.rename(video_temp, final_video_path)
                    self.logger.info(f"Saved silent video to {final_video_path}")

            if download_type in ["full", "audio"]:
                # Download audio stream
                audio_url = video_info["playinfo"]["data"]["dash"]["audio"][0][
                    "baseUrl"
                ]
                self.logger.info(
                    f"音频URL: {audio_url[:100]}..."
                )  # 只打印前100个字符，避免日志过长
                audio_success = self._download_stream(audio_url, audio_temp)

                # 记录音频下载结果
                try:
                    from src.core.logger import log_download_detail

                    log_download_detail(
                        "audio",
                        success=audio_success,
                        url=audio_url,
                        title=video_info.get("title", "未知标题"),
                    )
                except ImportError:
                    pass

                if not audio_success:
                    self.logger.error("Failed to download audio stream")
                    success = False

                # If audio only, rename the temp file to final output
                if download_type == "audio" and audio_success:
                    final_audio_path = final_path + ".mp3"
                    os.rename(audio_temp, final_audio_path)
                    self.logger.info(f"Saved audio to {final_audio_path}")

            # Merge audio and video if full download is requested
            if download_type == "full" and success:
                # 确保最终输出文件有正确的扩展名
                final_output = final_path + ".mp4"
                merge_success = self._merge_audio_video(
                    video_temp, audio_temp, final_output, ffmpeg_path
                )

                # 记录FFmpeg合并结果
                try:
                    from src.core.logger import log_download_detail

                    log_download_detail(
                        "ffmpeg",
                        success=merge_success,
                        path=final_output,
                        ffmpeg_path=ffmpeg_path,
                    )
                except ImportError:
                    pass

                if not merge_success:
                    self.logger.warning(
                        "Failed to merge audio and video, saving separate files"
                    )
                    # Save separate files if merge fails
                    final_video_path = final_path + ".mp4"
                    final_audio_path = final_path + ".mp3"
                    os.rename(video_temp, final_video_path)
                    os.rename(audio_temp, final_audio_path)
                    self.logger.info(
                        f"Saved video to {final_video_path} and audio to {final_audio_path}"
                    )
                    success = False

            # Clean up temporary files
            for temp_file in [video_temp, audio_temp]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)

            return success

        except Exception as e:
            self.logger.error(f"Failed to download video {url}: {e}")
            # 记录整体下载失败
            try:
                from src.core.logger import log_download_detail

                log_download_detail(
                    "title", "下载过程中出错", success=False, title=str(e)
                )
            except ImportError:
                pass
            return False

    def _download_stream(self, url: str, save_path: str) -> bool:
        """
        Download a single stream (video or audio).

        Args:
            url (str): Stream URL to download
            save_path (str): Path to save the downloaded stream

        Returns:
            bool: True if download successful, False otherwise
        """
        max_retries = 3
        retry_count = 0

        # 获取断点续传块大小设置 (MB转换为字节)
        resume_chunk_size_mb = 10  # 默认值
        if self.config_manager:
            try:
                resume_chunk_size_mb = self.config_manager.get_resume_chunk_size()
            except ValueError:
                pass
        resume_chunk_size_bytes = resume_chunk_size_mb * 1024 * 1024  # 转换为字节

        self.logger.info(f"下载流: {os.path.basename(save_path)}")
        self.logger.info(f"完整URL: {url}")

        while retry_count < max_retries:
            try:
                self.logger.info(
                    f"开始下载: {os.path.basename(save_path)}{' (重试 #' + str(retry_count + 1) + ')' if retry_count > 0 else ''}"
                )

                # 准备请求头
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Referer": "https://www.bilibili.com",
                    "Origin": "https://www.bilibili.com",
                    "Accept": "*/*",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Range": "bytes=0-",  # 支持断点续传
                }

                # 检查是否存在部分下载的文件
                downloaded = 0
                if os.path.exists(save_path):
                    downloaded = os.path.getsize(save_path)
                    if downloaded > 0:
                        headers["Range"] = f"bytes={downloaded}-"
                        self.logger.info(
                            f"断点续传: 从 {self._format_size(downloaded)} 开始"
                        )

                self.logger.info(f"发送HTTP请求: {url[:50]}...")
                response = self.session.get(
                    url, headers=headers, stream=True, timeout=30
                )
                response.raise_for_status()

                # 获取文件大小（如果服务器提供）
                total_size = int(response.headers.get("content-length", 0))
                if "content-range" in response.headers:
                    content_range = response.headers.get("content-range")
                    total_size = (
                        int(content_range.split("/")[-1])
                        if "/" in content_range
                        else total_size
                    )

                if total_size:
                    self.logger.info(f"文件大小: {self._format_size(total_size)}")

                # 下载文件
                mode = "ab" if downloaded > 0 else "wb"
                self.logger.info(f"开始写入文件: {save_path}")
                with open(save_path, mode) as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                            # 每下载指定大小记录一次进度
                            if downloaded % resume_chunk_size_bytes < 8192:
                                if total_size:
                                    percent = (downloaded / total_size) * 100
                                    self.logger.info(
                                        f"下载进度: {percent:.1f}% ({self._format_size(downloaded)}/{self._format_size(total_size)})"
                                    )
                                else:
                                    self.logger.info(
                                        f"已下载: {self._format_size(downloaded)}"
                                    )

                # 验证文件大小
                if total_size and os.path.exists(save_path):
                    file_size = os.path.getsize(save_path)
                    if file_size != total_size:
                        self.logger.warning(
                            f"文件大小不匹配: 期望 {self._format_size(total_size)}, 实际 {self._format_size(file_size)}"
                        )
                    else:
                        self.logger.info(
                            f"文件大小验证成功: {self._format_size(file_size)}"
                        )

                self.logger.info(f"下载完成: {os.path.basename(save_path)}")
                self.logger.info(f"保存路径: {save_path}")
                return True

            except requests.exceptions.RequestException as e:
                retry_count += 1
                self.logger.warning(f"下载失败 (尝试 {retry_count}/{max_retries}): {e}")
                if retry_count >= max_retries:
                    self.logger.error(f"达到最大重试次数，下载失败: {e}")
                    return False
                time.sleep(2)  # 重试前等待2秒
            except Exception as e:
                self.logger.error(f"下载失败: {e}")
                return False

        return False

    def _format_size(self, size_bytes):
        """将字节大小格式化为人类可读的形式"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    def _merge_audio_video(
        self, video_path: str, audio_path: str, output_path: str, ffmpeg_path: str
    ) -> bool:
        """
        Merge video and audio streams using FFmpeg.

        Args:
            video_path (str): Path to video file
            audio_path (str): Path to audio file
            output_path (str): Path for merged output file
            ffmpeg_path (str): Path to FFmpeg executable

        Returns:
            bool: True if merge successful, False otherwise
        """
        try:
            self.logger.info("开始合并音视频:")
            self.logger.info(f"- 视频文件: {video_path}")
            self.logger.info(f"- 音频文件: {audio_path}")
            self.logger.info(f"- 输出文件: {output_path}")
            self.logger.info(f"- FFmpeg路径: {ffmpeg_path}")

            # 检查文件是否存在
            if not os.path.exists(video_path):
                self.logger.error(f"视频文件不存在: {video_path}")
                return False

            if not os.path.exists(audio_path):
                self.logger.error(f"音频文件不存在: {audio_path}")
                return False

            # 检查文件大小
            video_size = os.path.getsize(video_path)
            audio_size = os.path.getsize(audio_path)
            self.logger.info(f"视频文件大小: {self._format_size(video_size)}")
            self.logger.info(f"音频文件大小: {self._format_size(audio_size)}")

            # Validate FFmpeg path
            if not ffmpeg_path:
                self.logger.error(f"FFmpeg路径未提供,path:{ffmpeg_path}")
                return False

            if not os.path.exists(ffmpeg_path):
                self.logger.error(f"FFmpeg不存在于: {ffmpeg_path}")
                return False

            # Check if FFmpeg is executable
            if not os.access(ffmpeg_path, os.X_OK):
                self.logger.error(f"FFmpeg没有执行权限: {ffmpeg_path}")
                return False

            cmd = [
                ffmpeg_path,
                "-i",
                video_path,
                "-i",
                audio_path,
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-strict",
                "experimental",
                "-y",  # Overwrite output file
                output_path,
            ]

            self.logger.info(f"执行FFmpeg命令: {' '.join(cmd)}")

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                # 检查输出文件是否存在和大小
                if os.path.exists(output_path):
                    output_size = os.path.getsize(output_path)
                    self.logger.info(
                        f"合并成功! 输出文件大小: {self._format_size(output_size)}"
                    )
                    self.logger.info(f"文件已保存到: {output_path}")
                    return True
                else:
                    self.logger.error(f"FFmpeg执行成功但输出文件不存在: {output_path}")
                    return False
            else:
                self.logger.error(f"FFmpeg合并失败: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"合并音视频失败: {e}")
            return False

    def download_series(
        self, series_url: str, save_path: str, ffmpeg_path: str = None
    ) -> bool:
        """
        Download a series of videos from Bilibili.

        Args:
            series_url (str): URL of the first video in the series
            save_path (str): Base path to save the series
            ffmpeg_path (str, optional): Path to FFmpeg executable

        Returns:
            bool: True if series download successful, False otherwise
        """
        try:
            # If FFmpeg path not provided, get from config
            if not ffmpeg_path and self.config_manager:
                ffmpeg_path = self.config_manager.get_ffmpeg_path()

            # Get first video info to determine series name
            first_video_info = self.get_video_info(series_url)
            if not first_video_info["playinfo"]:
                self.logger.error("Failed to extract first video information")
                return False

            # Extract series name from first video title
            series_title = self._extract_series_title(first_video_info["title"])

            # Create series folder
            if self.config_manager:
                # Use config manager to create series folder
                series_path = self.config_manager.get_series_download_path(
                    self.config_manager.get_default_category(), series_title
                )
            else:
                # Create series folder directly in save path
                series_path = os.path.join(save_path, series_title)
                os.makedirs(series_path, exist_ok=True)

            # Count total pages first
            base_url = series_url.split("?")[0]
            total_pages = 1

            # Try to find total page count
            try:
                response = self.session.get(series_url)
                page_match = re.search(r"共(\d+)P", response.text)
                if page_match:
                    total_pages = int(page_match.group(1))
            except ValueError:
                pass

            self.logger.info(
                f"Starting series download: {series_title} ({total_pages} parts)"
            )

            # Start downloading
            for page in range(1, total_pages + 1):
                page_url = f"{base_url}?p={page}"
                page_title = f"{series_title}_P{page:02d}"
                page_path = os.path.join(series_path, f"{page_title}.mp4")

                self.logger.info(f"Downloading part {page}/{total_pages}: {page_title}")

                if self.download_video(page_url, page_path, ffmpeg_path):
                    self.logger.info(f"Successfully downloaded part {page}")
                else:
                    self.logger.error(f"Failed to download part {page}")

                # Avoid requesting too fast
                time.sleep(random.uniform(1, 3))

            return True

        except Exception as e:
            self.logger.error(f"Failed to download series {series_url}: {e}")
            return False

    def _extract_series_title(self, title: str) -> str:
        """
        Extract series name from video title.

        Args:
            title (str): Full video title

        Returns:
            str: Extracted series name
        """
        # Remove common part indicators
        title = re.sub(r"[Pp]art\s*\d+", "", title)
        title = re.sub(r"第\s*\d+[话集]", "", title)
        title = re.sub(r"[Pp]\s*\d+", "", title)

        # Clean up extra spaces and punctuation
        title = re.sub(r"\s+", " ", title)
        title = re.sub(r"[^\w\s\u4e00-\u9fff]", "", title)
        title = title.strip()

        # If cleaned title is empty, return original
        if not title:
            return title

        return title
