# backend/services/supabase_service.py

from datetime import datetime
import json

class SupabaseService:
    @staticmethod
    def update_channel_info(supabase, channel_id, channel_title, channel_url, channel_description, total_videos, subscribers, num_retrieved_videos, top_video_ids):
        supabase.table('channels').upsert({
            'channel_id': channel_id,
            'channel_name': channel_title,
            'link_to_channel': channel_url,
            'about': channel_description,
            'number_of_total_videos': total_videos,
            'number_of_retrieved_videos': num_retrieved_videos,
            'ids_of_retrieved_videos': json.dumps(top_video_ids),
            'subscribers': subscribers,
            'channel_retrieval_date': datetime.utcnow().isoformat()
        }).execute()

    @staticmethod
    def insert_videos(supabase, videos):
        supabase.table('videos').upsert(videos).execute()

    @staticmethod
    def insert_comments(supabase, comments):
        supabase.table('comments').upsert(comments).execute()

    @staticmethod
    def insert_tags(supabase, video_id, tags):
        for tag in tags:
            supabase.table('tags').insert({
                'video_id': video_id,
                'tag': tag,
                'processed_date': datetime.utcnow().isoformat()
            }).execute()

    @staticmethod
    def update_video_tags(supabase, video_id, tags):
        supabase.table('videos').update({
            'tags': ", ".join(tags),
        }).eq('video_id', video_id).execute()