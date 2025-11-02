"""
Stream Handler - Extracts M3U8 link and processes live stream
Updated to handle rendition links that expire
"""
import subprocess
import time
import os
import re
import requests
import m3u8
from datetime import datetime
from stream_config import *

class StreamHandler:
    def __init__(self):
        self.is_running = False
        self.process = None
        self.m3u8_url = None
        self.current_chunk = 0
        self.last_m3u8_fetch = 0
        self.m3u8_refresh_interval = 300  # Refresh every 5 minutes
        
    def find_m3u8_link(self, page_url):
        """
        Find M3U8 stream link from the live page
        Returns RENDITION link, not manifest
        """
        try:
            print(f"🔍 Fetching page: {page_url}")
            
            # Add headers to mimic browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Referer': page_url
            }
            
            response = requests.get(page_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Look for m3u8 URLs in page source
            m3u8_pattern = r'https?://[^\s<>"]+?\.m3u8[^\s<>"\']*'
            matches = re.findall(m3u8_pattern, response.text)
            
            if matches:
                print(f"✅ Found {len(matches)} M3U8 link(s)")
                
                # Try to find rendition links (not master/manifest)
                rendition_url = self.get_rendition_link(matches, headers)
                
                if rendition_url:
                    self.m3u8_url = rendition_url
                    self.last_m3u8_fetch = time.time()
                    print(f"✅ Using rendition link: {self.m3u8_url}")
                    return self.m3u8_url
                else:
                    # Fallback to first match
                    self.m3u8_url = matches[0]
                    self.last_m3u8_fetch = time.time()
                    print(f"⚠️ Using first M3U8 link: {self.m3u8_url}")
                    return self.m3u8_url
            
            # Alternative: Look for iframe or video sources
            print("🔍 Checking iframes for M3U8 links...")
            iframe_pattern = r'<iframe[^>]+src=["\'](https?://[^"\']+)["\']'
            iframe_matches = re.findall(iframe_pattern, response.text)
            
            for iframe_url in iframe_matches:
                try:
                    print(f"📺 Checking iframe: {iframe_url}")
                    iframe_response = requests.get(iframe_url, headers=headers, timeout=10)
                    m3u8_in_iframe = re.findall(m3u8_pattern, iframe_response.text)
                    
                    if m3u8_in_iframe:
                        rendition_url = self.get_rendition_link(m3u8_in_iframe, headers)
                        if rendition_url:
                            self.m3u8_url = rendition_url
                            self.last_m3u8_fetch = time.time()
                            print(f"✅ Found rendition in iframe: {self.m3u8_url}")
                            return self.m3u8_url
                except Exception as e:
                    print(f"⚠️ Error fetching iframe: {e}")
                    continue
            
            print("❌ No M3U8 link found")
            return None
                
        except Exception as e:
            print(f"❌ Error finding M3U8 link: {e}")
            return None
    
    def get_rendition_link(self, m3u8_urls, headers):
        """
        Get rendition (actual stream) link from M3U8 URLs
        Avoids master/manifest playlists
        """
        for url in m3u8_urls:
            try:
                # Skip if it looks like a manifest
                if 'master' in url.lower() or 'manifest' in url.lower():
                    print(f"⏭️ Skipping manifest: {url}")
                    continue
                
                print(f"🔍 Checking M3U8: {url}")
                
                # Fetch and parse M3U8
                response = requests.get(url, headers=headers, timeout=5)
                playlist = m3u8.loads(response.text)
                
                # Check if it's a master playlist (has other playlists)
                if playlist.is_variant:
                    print(f"📋 Found master playlist with {len(playlist.playlists)} variants")
                    
                    # Get the best quality rendition
                    if playlist.playlists:
                        # Sort by bandwidth (highest first)
                        best_playlist = sorted(
                            playlist.playlists, 
                            key=lambda p: p.stream_info.bandwidth if p.stream_info.bandwidth else 0,
                            reverse=True
                        )[0]
                        
                        # Construct full URL if relative
                        rendition_url = best_playlist.absolute_uri or best_playlist.uri
                        if not rendition_url.startswith('http'):
                            base_url = url.rsplit('/', 1)[0]
                            rendition_url = f"{base_url}/{rendition_url}"
                        
                        print(f"✅ Found best rendition: {rendition_url}")
                        return rendition_url
                else:
                    # This is already a rendition link
                    print(f"✅ This is a rendition link: {url}")
                    return url
                    
            except Exception as e:
                print(f"⚠️ Error parsing {url}: {e}")
                continue
        
        return None
    
    def refresh_m3u8_if_needed(self):
        """
        Refresh M3U8 link if it's been too long (links expire)
        """
        current_time = time.time()
        time_since_fetch = current_time - self.last_m3u8_fetch
        
        if time_since_fetch > self.m3u8_refresh_interval:
            print(f"🔄 M3U8 link is {int(time_since_fetch)}s old, refreshing...")
            new_url = self.find_m3u8_link(STREAM_URL)
            if new_url:
                print("✅ M3U8 link refreshed successfully")
                return True
            else:
                print("⚠️ Could not refresh M3U8 link, using old one")
                return False
        return True
    
    def start_stream(self):
        """
        Start capturing the live stream
        """
        if self.is_running:
            print("⚠️ Stream already running")
            return False
        
        # Find M3U8 link
        if not self.m3u8_url:
            m3u8 = self.find_m3u8_link(STREAM_URL)
            if not m3u8:
                print("❌ Failed to find M3U8 link")
                return False
        
        self.is_running = True
        self.current_chunk = 0
        print(f"✅ Stream ready: {self.m3u8_url}")
        return True
    
    def extract_audio_chunk(self):
        """
        Extract a 1-minute audio chunk from the live stream using FFmpeg
        Auto-refreshes M3U8 link if needed
        """
        if not self.is_running:
            return None
        
        # Refresh M3U8 if needed
        self.refresh_m3u8_if_needed()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(AUDIO_CHUNKS_DIR, f"chunk_{timestamp}.wav")
        
        try:
            # FFmpeg command to extract 60 seconds of audio
            command = [
                'ffmpeg',
                '-headers', f'User-Agent: Mozilla/5.0\r\nReferer: {STREAM_URL}\r\n',  # Add headers
                '-i', self.m3u8_url,
                '-t', str(CHUNK_DURATION),  # Duration: 60 seconds
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # Audio codec
                '-ar', str(SAMPLE_RATE),  # Sample rate: 16000 Hz
                '-ac', '1',  # Mono audio
                '-y',  # Overwrite output file
                output_file
            ]
            
            print(f"📹 Extracting audio chunk {self.current_chunk + 1}...")
            print(f"🔗 Using M3U8: {self.m3u8_url[:80]}...")
            start_time = time.time()
            
            # Run FFmpeg
            result = subprocess.run(
                command, 
                check=True, 
                capture_output=True, 
                timeout=CHUNK_DURATION + 30,
                text=True
            )
            
            end_time = time.time()
            extraction_time = end_time - start_time
            
            # Check if file was created and has content
            if not os.path.exists(output_file) or os.path.getsize(output_file) < 1000:
                print("❌ Audio file is empty or not created")
                return None
            
            self.current_chunk += 1
            
            print(f"✅ Audio chunk extracted in {extraction_time:.2f}s: {output_file}")
            print(f"📊 File size: {os.path.getsize(output_file) / 1024 / 1024:.2f} MB")
            
            return {
                'file_path': output_file,
                'timestamp': timestamp,
                'chunk_number': self.current_chunk,
                'extraction_time': extraction_time
            }
            
        except subprocess.TimeoutExpired:
            print("❌ FFmpeg timeout - trying to refresh M3U8 link...")
            # Try to refresh M3U8 for next attempt
            self.last_m3u8_fetch = 0  # Force refresh
            return None
        except subprocess.CalledProcessError as e:
            print(f"❌ FFmpeg error: {e.stderr if e.stderr else str(e)}")
            # Check if it's a 403 error
            if "403" in str(e.stderr):
                print("🔄 Got 403 error, refreshing M3U8 link...")
                self.last_m3u8_fetch = 0  # Force refresh on next attempt
            return None
        except Exception as e:
            print(f"❌ Error extracting audio: {e}")
            return None
    
    def stop_stream(self):
        """
        Stop the stream capture
        """
        self.is_running = False
        if self.process:
            self.process.terminate()
            self.process = None
        print("🛑 Stream stopped")
        return True
    
    def get_status(self):
        """
        Get current stream status
        """
        return {
            'is_running': self.is_running,
            'chunks_processed': self.current_chunk,
            'm3u8_url': self.m3u8_url,
            'last_refresh': time.time() - self.last_m3u8_fetch if self.last_m3u8_fetch > 0 else None
        }