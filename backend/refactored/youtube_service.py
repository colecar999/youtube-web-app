# backend/services/youtube_service.py

import requests
from datetime import datetime
from config import YOUTUBE_API_KEY

class YouTubeService:
    @staticmethod
    def get_video_info(video_id):
        video_info_url = 'https://www.googleapis.com/youtube/v3/videos'
        params = {
            'part': 'snippet',
            'id': video_id,
            'key': YOUTUBE_API_KEY
        }
        response = requests.get(video_info_url, params=params)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_top_videos(channel_id, num_videos):
        search_url = 'https://www.googleapis.com/youtube/v3/search'
        search_params = {
            'part': 'id',
            'channelId': channel_id,
            'maxResults': num_videos,
            'order': 'viewCount',
            'type': 'video',
            'key': YOUTUBE_API_KEY
        }
        search_response = requests.get(search_url, params=search_params)
        search_response.raise_for_status()
        search_data = search_response.json()
        return [item['id']['videoId'] for item in search_data['items']]

    @staticmethod
    def get_videos_details(video_ids):
        videos_info_url = 'https://www.googleapis.com/youtube/v3/videos'
        videos_params = {
            'part': 'snippet,statistics,contentDetails',
            'id': ','.join(video_ids),
            'key': YOUTUBE_API_KEY
        }
        videos_response = requests.get(videos_info_url, params=videos_params)
        videos_response.raise_for_status()
        videos_data = videos_response.json()
        
        videos = []
        for item in videos_data['items']:
            snippet = item['snippet']
            statistics = item.get('statistics', {})
            content_details = item.get('contentDetails', {})
            videos.append({
                'video_id': item['id'],
                'title': snippet['title'],
                'description': snippet.get('description', ''),
                'duration': content_details.get('duration', 'N/A'),
                'view_count': int(statistics.get('viewCount', 0)),
                'like_count': int(statistics.get('likeCount', 0)),
                'comment_count': int(statistics.get('commentCount', 0)),
                'retrieval_date': datetime.utcnow().isoformat()
            })
        return videos

    @staticmethod
    def get_channel_stats(channel_id):
        channel_stats_url = 'https://www.googleapis.com/youtube/v3/channels'
        channel_stats_params = {
            'part': 'statistics',
            'id': channel_id,
            'key': YOUTUBE_API_KEY
        }
        channel_stats_response = requests.get(channel_stats_url, params=channel_stats_params)
        channel_stats_response.raise_for_status()
        channel_stats_data = channel_stats_response.json()
        
        channel_stats = channel_stats_data['items'][0]['statistics']
        return {
            'total_videos': int(channel_stats.get('videoCount', 0)),
            'subscribers': int(channel_stats.get('subscriberCount', 0))
        }

    @staticmethod
    def get_video_comments(video_id, num_comments):
        comments_url = 'https://www.googleapis.com/youtube/v3/commentThreads'
        comments_params = {
            'part': 'snippet,replies',
            'videoId': video_id,
            'maxResults': num_comments,
            'order': 'relevance',
            'key': YOUTUBE_API_KEY
        }
        comments_response = requests.get(comments_url, params=comments_params)
        comments_response.raise_for_status()
        comments_data = comments_response.json()
        
        comments = []
        for item in comments_data['items']:
            comment = item['snippet']['topLevelComment']['snippet']
            comments.append({
                'video_id': video_id,
                'comment_id': item['id'],
                'comment_author': comment.get('authorDisplayName', ''),
                'comment_likes': int(comment.get('likeCount', 0)),
                'comment_published_at': comment.get('publishedAt', ''),
                'comment_updated_at': comment.get('updatedAt', ''),
                'comment_parent_id': '',  # Top-level comment, no parent
                'comment_text': comment.get('textOriginal', ''),
                'comment_retrieval_date': datetime.utcnow().isoformat()
            })
            
            # Process reply comments
            if 'replies' in item:
                for reply in item['replies']['comments']:
                    reply_snippet = reply['snippet']
                    comments.append({
                        'video_id': video_id,
                        'comment_id': reply['id'],
                        'comment_author': reply_snippet.get('authorDisplayName', ''),
                        'comment_likes': int(reply_snippet.get('likeCount', 0)),
                        'comment_published_at': reply_snippet.get('publishedAt', ''),
                        'comment_updated_at': reply_snippet.get('updatedAt', ''),
                        'comment_parent_id': item['id'],  # Parent comment ID
                        'comment_text': reply_snippet.get('textOriginal', ''),
                        'comment_retrieval_date': datetime.utcnow().isoformat()
                    })

            # Break the loop if we've reached the desired number of comments
            if len(comments) >= num_comments:
                break
        
        # Truncate comments list if it exceeds num_comments
        return comments[:num_comments]