"""
B站视频下载器核心类
"""
import os
import re
import json
import time
import random
import requests
from typing import Optional, Dict, Any
from tqdm import tqdm
import subprocess

from .logger import get_logger


class BiliDownloader:
    """B站视频下载器核心类"""
    
    def __init__(self, config_manager=None):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        ]
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents)
        })
        self.config_manager = config_manager
        self.logger = get_logger("BiliDownloader")
        self.logger.info("B站下载器初始化完成")
    
    def get_video_info(self, url: str, cookie: str = "") -> Optional[Dict[str, Any]]:
        """获取视频信息"""
        try:
            self.logger.info(f"开始获取视频信息: {url}")
            
            if cookie:
                self.session.headers.update({'Cookie': cookie})
                self.logger.debug("已设置Cookie")
            
            # 处理分P视频
            page_count = 1
            new_url = re.sub(r"\?.*", "?p=1", url)
            
            while True:
                new_url = re.sub(r"p=\d+", f"p={page_count}", new_url)
                self.logger.debug(f"尝试获取第{page_count}P: {new_url}")
                
                resp = self.session.get(new_url)
                if resp.status_code != 200:
                    self.logger.warning(f"第{page_count}P请求失败，状态码: {resp.status_code}")
                    break
                
                page_content = resp.text
                
                # 提取视频标题
                title_match = re.search(r'<title data-vue-meta="true">(?P<title>.*?)</title>', page_content)
                if not title_match:
                    self.logger.warning(f"第{page_count}P无法提取标题")
                    break
                
                title = title_match.group('title')
                self.logger.info(f"获取到标题: {title}")
                
                # 提取播放信息
                playinfo_match = re.search(r'<script>window.__playinfo__=(?P<data>.*?)</script>', page_content)
                if not playinfo_match:
                    self.logger.warning(f"第{page_count}P无法提取播放信息")
                    break
                
                try:
                    playinfo = json.loads(playinfo_match.group('data'))
                    video_url = playinfo['data']['dash']['video'][0]['baseUrl']
                    audio_url = playinfo['data']['dash']['audio'][0]['baseUrl']
                    
                    self.logger.info(f"成功提取第{page_count}P的播放信息")
                    
                    return {
                        'title': title,
                        'video_url': video_url,
                        'audio_url': audio_url,
                        'page': page_count,
                        'url': new_url
                    }
                except (json.JSONDecodeError, KeyError) as e:
                    self.logger.warning(f"第{page_count}P播放信息解析失败: {e}")
                    break
                
                page_count += 1
                
        except Exception as e:
            self.logger.error(f"获取视频信息失败: {e}")
            return None
        
        return None
    
    def download_video(self, video_info: Dict[str, Any], save_path: str, 
                      ffmpeg_path: str = None, progress_callback=None) -> bool:
        """下载视频"""
        try:
            # 如果没有提供FFmpeg路径，从配置中获取
            if not ffmpeg_path and hasattr(self, 'config_manager') and self.config_manager:
                ffmpeg_path = self.config_manager.get_ffmpeg_path()
                self.logger.info(f"从配置中获取FFmpeg路径: {ffmpeg_path}")
            
            title = video_info['title']
            video_url = video_info['video_url']
            audio_url = video_info['audio_url']
            page = video_info['page']
            
            self.logger.info(f"开始下载视频: {title} (第{page}P)")
            self.logger.download_info(f"开始下载: {title} (第{page}P)")
            
            # 创建临时文件路径
            video_temp = os.path.join(save_path, 'video_temp.mp4')
            audio_temp = os.path.join(save_path, 'audio_temp.mp3')
            final_path = os.path.join(save_path, f'{title}_P{page}.mp4')
            
            self.logger.debug(f"临时文件路径: 视频={video_temp}, 音频={audio_temp}")
            self.logger.debug(f"最终文件路径: {final_path}")
            
            # 下载视频流
            if progress_callback:
                progress_callback(0, "开始下载视频流...")
            
            self.logger.info("开始下载视频流...")
            video_success = self._download_stream(video_url, video_temp, progress_callback, "视频")
            
            if not video_success:
                self.logger.error("视频流下载失败")
                return False
            
            # 下载音频流
            if progress_callback:
                progress_callback(50, "开始下载音频流...")
            
            self.logger.info("开始下载音频流...")
            audio_success = self._download_stream(audio_url, audio_temp, progress_callback, "音频")
            
            if not audio_success:
                self.logger.error("音频流下载失败")
                return False
            
            # 合并音视频
            if progress_callback:
                progress_callback(90, "正在合并音视频...")
            
            self.logger.info("开始合并音视频...")
            success = self._merge_audio_video(video_temp, audio_temp, final_path, ffmpeg_path)
            
            if success:
                self.logger.info(f"视频合并成功: {final_path}")
                self.logger.download_info(f"下载完成: {title} (第{page}P)")
            else:
                self.logger.error("视频合并失败")
            
            # 清理临时文件
            if os.path.exists(video_temp):
                os.remove(video_temp)
                self.logger.debug("已清理临时视频文件")
            if os.path.exists(audio_temp):
                os.remove(audio_temp)
                self.logger.debug("已清理临时音频文件")
            
            if progress_callback:
                progress_callback(100, "下载完成！")
            
            return success
            
        except Exception as e:
            self.logger.error(f"下载失败: {e}")
            return False
    
    def _download_stream(self, url: str, file_path: str, 
                        progress_callback=None, stream_type: str = "文件") -> bool:
        """下载流文件"""
        try:
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Referer': 'https://www.bilibili.com/'
            }
            
            response = self.session.get(url, headers=headers, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            
            with open(file_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            progress_callback(progress, f"下载{stream_type}中... {downloaded}/{total_size} bytes")
            
            return True
            
        except Exception as e:
            self.logger.error(f"下载{stream_type}失败: {e}")
            return False
    
    def _merge_audio_video(self, video_path: str, audio_path: str, 
                           output_path: str, ffmpeg_path: str) -> bool:
        """合并音视频"""
        try:
            # 验证FFmpeg路径
            if not ffmpeg_path or not ffmpeg_path.strip():
                self.logger.error("FFmpeg路径未设置，无法合并音视频")
                return False
            
            if not os.path.exists(ffmpeg_path):
                self.logger.error(f"FFmpeg路径不存在: {ffmpeg_path}")
                return False
            
            # 检查FFmpeg是否可执行
            if not os.access(ffmpeg_path, os.X_OK):
                self.logger.error(f"FFmpeg文件不可执行: {ffmpeg_path}")
                return False
            
            self.logger.info(f"使用FFmpeg路径: {ffmpeg_path}")
            
            cmd = [
                ffmpeg_path,
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'copy',
                '-c:a', 'copy',
                '-y',  # 覆盖输出文件
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info("FFmpeg合并成功")
                return True
            else:
                self.logger.error(f"FFmpeg合并失败: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"合并音视频失败: {e}")
            return False
    
    def download_series(self, base_url: str, save_path: str, ffmpeg_path: str = None,
                        cookie: str = "", progress_callback=None, category_name: str = "default") -> bool:
        """下载系列视频"""
        try:
            # 如果没有提供FFmpeg路径，从配置中获取
            if not ffmpeg_path and hasattr(self, 'config_manager') and self.config_manager:
                ffmpeg_path = self.config_manager.get_ffmpeg_path()
                self.logger.info(f"从配置中获取FFmpeg路径: {ffmpeg_path}")
            
            self.logger.info(f"开始下载系列视频: {base_url}")
            self.logger.info(f"分类: {category_name}, 保存路径: {save_path}")
            
            # 获取第一个视频信息来确定系列名称
            first_video_info = self.get_video_info(base_url, cookie)
            if not first_video_info:
                self.logger.error("无法获取系列视频信息")
                return False
            
            # 提取系列名称（从第一个视频标题中提取）
            series_title = self._extract_series_title(first_video_info['title'])
            self.logger.info(f"系列名称: {series_title}")
            
            # 创建系列文件夹
            if hasattr(self, 'config_manager') and self.config_manager:
                # 使用配置管理器创建系列文件夹
                series_save_path = self.config_manager.get_series_download_path(category_name, series_title)
            else:
                # 直接在保存路径下创建系列文件夹
                series_save_path = os.path.join(save_path, series_title)
                os.makedirs(series_save_path, exist_ok=True)
            
            self.logger.info(f"系列保存路径: {series_save_path}")
            
            page = 1
            success_count = 0
            total_pages = 0
            
            # 先统计总页数
            while True:
                url = re.sub(r"p=\d+", f"p={page}", base_url)
                if "?" not in url:
                    url += f"?p={page}"
                
                video_info = self.get_video_info(url, cookie)
                if not video_info:
                    break
                total_pages = page
                page += 1
                time.sleep(0.5)  # 避免请求过快
            
            self.logger.info(f"系列总页数: {total_pages}")
            
            # 开始下载
            page = 1
            while page <= total_pages:
                url = re.sub(r"p=\d+", f"p={page}", base_url)
                if "?" not in url:
                    url += f"?p={page}"
                
                video_info = self.get_video_info(url, cookie)
                if not video_info:
                    self.logger.warning(f"第{page}P获取失败，跳过")
                    page += 1
                    continue
                
                if progress_callback:
                    progress_callback(0, f"开始下载第{page}P: {video_info['title']}")
                
                self.logger.info(f"下载第{page}P: {video_info['title']}")
                
                # 下载到系列文件夹
                success = self.download_video(video_info, series_save_path, ffmpeg_path, progress_callback)
                if success:
                    success_count += 1
                    self.logger.info(f"第{page}P下载成功")
                else:
                    self.logger.warning(f"第{page}P下载失败")
                
                page += 1
                time.sleep(random.uniform(1, 3))  # 避免请求过快
            
            self.logger.info(f"系列下载完成，成功: {success_count}/{total_pages}")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"系列下载异常: {e}")
            return False
    
    def _extract_series_title(self, video_title: str) -> str:
        """从视频标题中提取系列名称"""
        try:
            # 移除常见的分P标识
            series_title = re.sub(r'[Pp]art\s*\d+', '', video_title)
            series_title = re.sub(r'第\s*\d+[Pp]', '', series_title)
            series_title = re.sub(r'[Pp]\s*\d+', '', series_title)
            series_title = re.sub(r'\(\d+\)', '', series_title)
            series_title = re.sub(r'【\d+】', '', series_title)
            
            # 清理多余的空格和标点
            series_title = re.sub(r'\s+', ' ', series_title)
            series_title = series_title.strip(' -_()【】')
            
            # 如果清理后为空，返回原标题
            if not series_title:
                return video_title
            
            return series_title
            
        except Exception as e:
            self.logger.warning(f"提取系列名称失败: {e}")
            return video_title 