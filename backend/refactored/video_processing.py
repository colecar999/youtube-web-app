# backend/tasks/video_processing.py

import logging
from services.youtube_service import YouTubeService
from services.transcript_service import TranscriptService
from tag_workflow import process_tags
from services.supabase_service import SupabaseService
from utils.helpers import send_update
from models.video import Video
from models.channel import Channel
from models.comment import Comment

logger = logging.getLogger(__name__)

async def process_videos(session_id: str, supabase, video_ids: list, num_videos: int, num_comments: int, num_tags: int, clustering_strength: float):
    logger.info("Starting process_videos function")
    try:
        success = await send_update(session_id, "Starting video processing...", supabase)
        if not success:
            logger.error(f"Failed to send initial update for session {session_id}")

        for video_id in video_ids:
            logger.info(f"Processing video ID: {video_id}")
            try:
                # Step 1: Get channel ID from YouTube API
                video_info = YouTubeService.get_video_info(video_id)
                if not video_info['items']:
                    logger.warning(f"No data found for video ID: {video_id}")
                    await send_update(session_id, f"No data found for video ID: {video_id}", supabase)
                    continue

                snippet = video_info['items'][0]['snippet']
                channel_id = snippet['channelId']
                channel_title = snippet['channelTitle']
                channel_url = f"https://www.youtube.com/channel/{channel_id}"
                channel_description = snippet.get('description', '')

                # Step 2: Fetch top videos for the channel
                top_video_ids = YouTubeService.get_top_videos(channel_id, num_videos)

                # Step 3: Fetch detailed information for these videos
                videos_data = YouTubeService.get_videos_details(top_video_ids)

                # Fetch channel statistics
                channel_stats = YouTubeService.get_channel_stats(channel_id)

                # Update the channel information
                channel = Channel(channel_id, channel_title, channel_url, channel_description, 
                                  channel_stats['total_videos'], channel_stats['subscribers'])
                SupabaseService.update_channel_info(supabase, **channel.to_dict())

                await send_update(session_id, f"Updated channel info for {channel_title}", supabase)

                videos = [Video(**video_data) for video_data in videos_data]
                SupabaseService.insert_videos(supabase, [video.to_dict() for video in videos])
                await send_update(session_id, f"Saved channel and videos for channel ID: {channel_id}", supabase)

                # Step 5: Fetch and save comments for each video
                for video in videos:
                    comments_data = YouTubeService.get_video_comments(video.video_id, num_comments)
                    comments = [Comment(**comment_data) for comment_data in comments_data]
                    SupabaseService.insert_comments(supabase, [comment.to_dict() for comment in comments])
                    await send_update(session_id, f"Saved {len(comments)} comments for video ID: {video.video_id}", supabase)

                # Step 6: Process each video for transcription and tagging
                for video in videos:
                    try:
                        transcript_data = await TranscriptService.get_transcript(video.video_id, session_id, supabase)
                        if transcript_data:
                            transcript_text = ' '.join([entry['text'] for entry in transcript_data])
                            tags = TagService.generate_tags(transcript_text, num_tags=num_tags)
                            final_tags = TagService.process_tags(tags, clustering_strength)

                            SupabaseService.insert_tags(supabase, video.video_id, final_tags)
                            SupabaseService.update_video_tags(supabase, video.video_id, final_tags)

                            await send_update(session_id, f"Generated and stored {len(final_tags)} tags for video ID: {video.video_id}", supabase)
                    except Exception as e:
                        error_message = f"Error processing video ID {video.video_id}: {str(e)}"
                        logger.error(error_message)
                        await send_update(session_id, error_message, supabase)

            except Exception as e:
                error_message = f"Error processing video ID {video_id}: {str(e)}"
                logger.error(error_message)
                await send_update(session_id, error_message, supabase)

        await send_update(session_id, "Video processing completed.", supabase)
    except Exception as e:
        error_message = f"Error in process_videos: {str(e)}"
        logger.error(error_message)
        await send_update(session_id, error_message, supabase)