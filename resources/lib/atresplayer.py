"""
AtrésPlayer Scraper Module
Handles scraping of AtrésPlayer live channels and on-demand content
"""

import requests
import json
import logging

logger = logging.getLogger(__name__)

class AtresplayerScraper:
    def __init__(self):
        self.api_url = 'https://api.atresplayer.com'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        })
        self.access_token = None
    
    def authenticate(self, username, password):
        """Authenticate user and get access token"""
        try:
            auth_url = f'{self.api_url}/v1/login'
            payload = {
                'username': username,
                'password': password
            }
            response = self.session.post(auth_url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'token' in data:
                self.access_token = data['token']
                self.session.headers['Authorization'] = f'Bearer {self.access_token}'
                logger.info("Authentication successful")
                return True
            
            return False
        
        except requests.RequestException as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def get_live_channels(self):
        """Fetch live channels"""
        try:
            url = f'{self.api_url}/v1/channels'
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            channels = []
            if 'channels' in data:
                for channel in data['channels']:
                    ch = {
                        'id': channel.get('id'),
                        'title': channel.get('name', 'Unknown'),
                        'url': channel.get('stream_url'),
                        'icon': channel.get('image_url'),
                        'description': channel.get('description', '')
                    }
                    channels.append(ch)
            
            logger.info(f"Found {len(channels)} live channels")
            return channels
        
        except requests.RequestException as e:
            logger.error(f"Error fetching live channels: {e}")
            return []
    
    def get_on_demand(self):
        """Fetch on-demand content"""
        try:
            url = f'{self.api_url}/v1/videos'
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            videos = []
            if 'videos' in data:
                for video in data['videos']:
                    v = {
                        'id': video.get('id'),
                        'title': video.get('title', 'Unknown'),
                        'description': video.get('description', ''),
                        'icon': video.get('thumbnail'),
                        'url': video.get('url'),
                        'duration': video.get('duration')
                    }
                    videos.append(v)
            
            logger.info(f"Found {len(videos)} videos")
            return videos
        
        except requests.RequestException as e:
            logger.error(f"Error fetching on-demand content: {e}")
            return []
    
    def search(self, query):
        """Search for content"""
        try:
            url = f'{self.api_url}/v1/search'
            params = {'q': query}
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return data.get('results', [])
        
        except requests.RequestException as e:
            logger.error(f"Search error: {e}")
            return []
