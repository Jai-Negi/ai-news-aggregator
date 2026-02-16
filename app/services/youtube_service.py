"""
YouTube Service

Handles all interactions with YouTube Data API.

Features:
- Fetch videos from channels
- Get video transcripts/captions
- Extract video metadata
- Filter by date

Uses:
- YouTube Data API v3 (video metadata)
- youtube-transcript-api (transcripts)
"""

import os
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable
)

logger = logging.getLogger(__name__)


class YouTubeService:
    """
    Service for interacting with YouTube.
    
    Fetches videos and transcripts from YouTube channels.
    
    Example:
        youtube = YouTubeService()
        videos = youtube.get_channel_videos(
            channel_id="UCbfYPyITQ-7l4upoX8nvctg",
            max_results=1
        )
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize YouTube service.
        
        Args:
            api_key: YouTube API key. If not provided, reads from YOUTUBE_API_KEY env var.
        """
        # Get API key
        self.api_key = api_key or os.getenv('YOUTUBE_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "YouTube API key not found! "
                "Set YOUTUBE_API_KEY environment variable or pass api_key parameter."
            )
        
        # Build YouTube API client
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        
        # Initialize transcript API
        self.transcript_api = YouTubeTranscriptApi()
        
        logger.info("YouTubeService initialized successfully")
    
    def get_channel_videos(
        self,
        channel_id: str,
        max_results: int = 1,  # Default to 1 for production use
        published_after: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Get videos from a YouTube channel.
        
        Args:
            channel_id: YouTube channel ID (e.g., "UCbfYPyITQ-7l4upoX8nvctg")
            max_results: Maximum number of videos to return (default: 1)
            published_after: Only get videos published after this date
        
        Returns:
            list: List of video dictionaries with metadata and transcripts
        
        Example:
            videos = youtube.get_channel_videos(
                channel_id="UCbfYPyITQ-7l4upoX8nvctg",
                max_results=1,
                published_after=datetime(2026, 1, 20)
            )
        """
        try:
            # Get channel's uploads playlist ID
            channel_response = self.youtube.channels().list(
                part='contentDetails',
                id=channel_id
            ).execute()
            
            if not channel_response.get('items'):
                logger.warning(f"Channel not found: {channel_id}")
                return []
            
            # Get uploads playlist ID
            uploads_playlist_id = (
                channel_response['items'][0]
                ['contentDetails']
                ['relatedPlaylists']
                ['uploads']
            )
            
            # Get videos from uploads playlist
            videos = self._get_playlist_videos(
                uploads_playlist_id,
                max_results,
                published_after
            )
            
            logger.info(f"Fetched {len(videos)} videos from channel {channel_id}")
            return videos
            
        except Exception as e:
            logger.error(f"Failed to fetch videos from channel {channel_id}: {e}")
            return []
    
    def _get_playlist_videos(
        self,
        playlist_id: str,
        max_results: int,
        published_after: Optional[datetime]
    ) -> List[Dict]:
        """
        Get videos from a playlist.
        
        Internal method used by get_channel_videos.
        """
        videos = []
        next_page_token = None
        
        while len(videos) < max_results:
            try:
                # Request playlist items
                request = self.youtube.playlistItems().list(
                    part='snippet,contentDetails',
                    playlistId=playlist_id,
                    maxResults=min(50, max_results - len(videos)),
                    pageToken=next_page_token
                )
                
                response = request.execute()
                
                # Process each video
                for item in response.get('items', []):
                    video_data = self._process_video_item(item, published_after)
                    if video_data:
                        videos.append(video_data)
                        
                        if len(videos) >= max_results:
                            break
                
                # Check for more pages
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching playlist items: {e}")
                break
        
        return videos
    
    def _process_video_item(
        self,
        item: Dict,
        published_after: Optional[datetime]
    ) -> Optional[Dict]:
        """
        Process a single video item.
        
        Extracts metadata and transcript.
        """
        try:
            # Extract basic info
            video_id = item['contentDetails']['videoId']
            snippet = item['snippet']
            
            # Parse published date
            published_at = datetime.strptime(
                snippet['publishedAt'],
                '%Y-%m-%dT%H:%M:%SZ'
            )
            
            # Filter by date if specified
            if published_after and published_at < published_after:
                return None
            
            # Get video details
            video_response = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=video_id
            ).execute()
            
            if not video_response.get('items'):
                return None
            
            video_details = video_response['items'][0]
            
            # Get transcript
            transcript = self.get_video_transcript(video_id)
            
            # If no transcript, log but still return video metadata
            # (Changed: Don't skip video if transcript unavailable)
            if not transcript:
                logger.warning(f"No transcript for video {video_id}")
                # Still return video with empty transcript
                transcript = ""
            
            # Build video data
            video_data = {
                'id': video_id,
                'title': snippet['title'],
                'description': snippet.get('description', ''),
                'published_at': published_at,
                'channel_id': snippet['channelId'],
                'channel_title': snippet['channelTitle'],
                'url': f"https://www.youtube.com/watch?v={video_id}",
                'thumbnail': snippet['thumbnails']['high']['url'],
                'transcript': transcript,
                'duration': video_details['contentDetails']['duration'],
                'view_count': int(video_details['statistics'].get('viewCount', 0)),
                'like_count': int(video_details['statistics'].get('likeCount', 0)),
                'comment_count': int(video_details['statistics'].get('commentCount', 0))
            }
            
            return video_data
            
        except Exception as e:
            logger.error(f"Error processing video item: {e}")
            return None
    
    def get_video_transcript(self, video_id: str) -> Optional[str]:
        """
        Get transcript/captions for a video.
        
        Handles rate limiting and various error conditions gracefully.
        
        Args:
            video_id: YouTube video ID
        
        Returns:
            str: Full transcript text, or None if unavailable
        
        Example:
            transcript = youtube.get_video_transcript("dQw4w9WgXcQ")
        """
        try:
            # Fetch transcript using instance method (youtube-transcript-api 1.2.3)
            fetched_transcript = self.transcript_api.fetch(
                video_id=video_id,
                languages=['en', 'en-US', 'en-GB']
            )
            
            # FetchedTranscript is directly iterable
            # Each entry is a FetchedTranscriptSnippet with .text attribute
            transcript_text = ' '.join([
                entry.text for entry in fetched_transcript
            ])
            
            logger.info(f"Got transcript for {video_id} ({len(transcript_text)} chars)")
            return transcript_text
            
        except TranscriptsDisabled:
            logger.warning(f"Transcripts disabled for video {video_id}")
            return None
            
        except NoTranscriptFound:
            logger.warning(f"No transcript found for video {video_id}")
            return None
            
        except VideoUnavailable:
            logger.warning(f"Video unavailable: {video_id}")
            return None
            
        except Exception as e:
            # Better error handling for rate limiting
            error_msg = str(e).lower()
            
            if 'too many requests' in error_msg or 'rate limit' in error_msg:
                logger.warning(f"Rate limited for video {video_id} - temporary YouTube restriction")
            elif 'ip' in error_msg and ('block' in error_msg or 'ban' in error_msg):
                logger.warning(f"IP temporarily blocked for video {video_id} - wait 24 hours")
            elif 'could not retrieve' in error_msg:
                logger.warning(f"Could not retrieve transcript for {video_id} - may be rate limited")
            else:
                logger.error(f"Error getting transcript for {video_id}: {e}")
            
            return None
    
    def get_video_details(self, video_id: str) -> Optional[Dict]:
        """
        Get detailed info for a specific video.
        
        Args:
            video_id: YouTube video ID
        
        Returns:
            dict: Video details including transcript
        
        Example:
            details = youtube.get_video_details("dQw4w9WgXcQ")
        """
        try:
            # Get video info
            response = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=video_id
            ).execute()
            
            if not response.get('items'):
                logger.warning(f"Video not found: {video_id}")
                return None
            
            item = response['items'][0]
            snippet = item['snippet']
            
            # Get transcript
            transcript = self.get_video_transcript(video_id)
            
            # Build video data
            video_data = {
                'id': video_id,
                'title': snippet['title'],
                'description': snippet.get('description', ''),
                'published_at': datetime.strptime(
                    snippet['publishedAt'],
                    '%Y-%m-%dT%H:%M:%SZ'
                ),
                'channel_id': snippet['channelId'],
                'channel_title': snippet['channelTitle'],
                'url': f"https://www.youtube.com/watch?v={video_id}",
                'thumbnail': snippet['thumbnails']['high']['url'],
                'transcript': transcript or "",
                'duration': item['contentDetails']['duration'],
                'view_count': int(item['statistics'].get('viewCount', 0)),
                'like_count': int(item['statistics'].get('likeCount', 0)),
                'comment_count': int(item['statistics'].get('commentCount', 0))
            }
            
            logger.info(f"Fetched details for video {video_id}")
            return video_data
            
        except Exception as e:
            logger.error(f"Failed to get video details for {video_id}: {e}")
            return None
    
    def search_videos(
        self,
        query: str,
        max_results: int = 10,
        published_after: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Search for videos by keyword.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            published_after: Only get videos after this date
        
        Returns:
            list: List of video dictionaries
        
        Example:
            videos = youtube.search_videos("AI news", max_results=5)
        """
        try:
            # Build search parameters
            search_params = {
                'part': 'snippet',
                'q': query,
                'type': 'video',
                'maxResults': max_results,
                'order': 'date'
            }
            
            # Add date filter if specified
            if published_after:
                search_params['publishedAfter'] = published_after.isoformat() + 'Z'
            
            # Execute search
            response = self.youtube.search().list(**search_params).execute()
            
            # Process results
            videos = []
            for item in response.get('items', []):
                video_id = item['id']['videoId']
                video_data = self.get_video_details(video_id)
                
                if video_data:
                    videos.append(video_data)
            
            logger.info(f"Found {len(videos)} videos for query: {query}")
            return videos
            
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            return []
    
    def test_connection(self) -> bool:
        """
        Test if YouTube API connection works.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Try a simple API call
            response = self.youtube.videos().list(
                part='snippet',
                id='dQw4w9WgXcQ'  # Rick Astley - Never Gonna Give You Up
            ).execute()
            
            result = len(response.get('items', [])) > 0
            
            if result:
                logger.info("YouTube connection test: SUCCESS")
            else:
                logger.warning("YouTube connection test: UNEXPECTED RESPONSE")
            
            return result
            
        except Exception as e:
            logger.error(f"YouTube connection test FAILED: {e}")
            return False