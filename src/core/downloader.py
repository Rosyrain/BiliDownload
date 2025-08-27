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
import random
import requests
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from .logger import get_logger


class BiliDownloader:
    """
    Core downloader for Bilibili videos.
    
    Handles video information extraction, downloading of video/audio streams,
    and merging using FFmpeg. Supports both single videos and series.
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize the BiliDownloader with configuration manager.
        
        Args:
            config_manager: Configuration manager instance for settings
        """
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
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
            if '?p=' in url:
                url = url.split('?p=')[0]
            
            response = self.session.get(url)
            response.raise_for_status()
            
            # Extract video title
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', response.text)
            title = title_match.group(1).strip() if title_match else "Unknown Title"
            
            # Extract playback information
            playinfo_match = re.search(r'window\.__playinfo__=({.*?})</script>', response.text)
            if playinfo_match:
                import json
                playinfo = json.loads(playinfo_match.group(1))
                return {
                    'title': title,
                    'playinfo': playinfo,
                    'url': url
                }
            
            return {
                'title': title,
                'playinfo': None,
                'url': url
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get video info from {url}: {e}")
            return {
                'title': "Error",
                'playinfo': None,
                'url': url
            }
    
    def download_video(self, url: str, save_path: str, ffmpeg_path: str = None) -> bool:
        """
        Download a single Bilibili video.
        
        Args:
            url (str): Bilibili video URL
            save_path (str): Path to save the downloaded video
            ffmpeg_path (str, optional): Path to FFmpeg executable
            
        Returns:
            bool: True if download successful, False otherwise
        """
        try:
            # If FFmpeg path not provided, get from config
            if not ffmpeg_path and self.config_manager:
                ffmpeg_path = self.config_manager.get('DEFAULT', 'ffmpeg_path')
            
            video_info = self.get_video_info(url)
            if not video_info['playinfo']:
                self.logger.error("Failed to extract video information")
                return False
            
            # Create temporary file paths
            video_temp = save_path + '.video.tmp'
            audio_temp = save_path + '.audio.tmp'
            
            # Download video stream
            video_url = video_info['playinfo']['data']['dash']['video'][0]['baseUrl']
            self._download_stream(video_url, video_temp)
            
            # Download audio stream
            audio_url = video_info['playinfo']['data']['dash']['audio'][0]['baseUrl']
            self._download_stream(audio_url, audio_temp)
            
            # Merge audio and video
            success = self._merge_audio_video(video_temp, audio_temp, save_path, ffmpeg_path)
            
            # Clean up temporary files
            for temp_file in [video_temp, audio_temp]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to download video {url}: {e}")
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
        try:
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to download stream to {save_path}: {e}")
            return False
    
    def _merge_audio_video(self, video_path: str, audio_path: str, output_path: str, ffmpeg_path: str) -> bool:
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
            # Validate FFmpeg path
            if not ffmpeg_path:
                self.logger.error("FFmpeg path not provided")
                return False
            
            if not os.path.exists(ffmpeg_path):
                self.logger.error(f"FFmpeg not found at: {ffmpeg_path}")
                return False
            
            # Check if FFmpeg is executable
            if not os.access(ffmpeg_path, os.X_OK):
                self.logger.error(f"FFmpeg not executable at: {ffmpeg_path}")
                return False
            
            cmd = [
                ffmpeg_path,
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-strict', 'experimental',
                '-y',  # Overwrite output file
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Successfully merged video and audio to: {output_path}")
                return True
            else:
                self.logger.error(f"FFmpeg merge failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to merge audio and video: {e}")
            return False
    
    def download_series(self, series_url: str, save_path: str, ffmpeg_path: str = None) -> bool:
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
                ffmpeg_path = self.config_manager.get('DEFAULT', 'ffmpeg_path')
            
            # Get first video info to determine series name
            first_video_info = self.get_video_info(series_url)
            if not first_video_info['playinfo']:
                self.logger.error("Failed to extract first video information")
                return False
            
            # Extract series name from first video title
            series_title = self._extract_series_title(first_video_info['title'])
            
            # Create series folder
            if self.config_manager:
                # Use config manager to create series folder
                series_path = self.config_manager.get_series_download_path(
                    self.config_manager.get('DEFAULT', 'default_category'),
                    series_title
                )
            else:
                # Create series folder directly in save path
                series_path = os.path.join(save_path, series_title)
                os.makedirs(series_path, exist_ok=True)
            
            # Count total pages first
            base_url = series_url.split('?')[0]
            total_pages = 1
            
            # Try to find total page count
            try:
                response = self.session.get(series_url)
                page_match = re.search(r'共(\d+)P', response.text)
                if page_match:
                    total_pages = int(page_match.group(1))
            except:
                pass
            
            self.logger.info(f"Starting series download: {series_title} ({total_pages} parts)")
            
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
        title = re.sub(r'[Pp]art\s*\d+', '', title)
        title = re.sub(r'第\s*\d+[话集]', '', title)
        title = re.sub(r'[Pp]\s*\d+', '', title)
        
        # Clean up extra spaces and punctuation
        title = re.sub(r'\s+', ' ', title)
        title = re.sub(r'[^\w\s\u4e00-\u9fff]', '', title)
        title = title.strip()
        
        # If cleaned title is empty, return original
        if not title:
            return title
        
        return title 