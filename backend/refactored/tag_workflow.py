# youtube-web-app/backend/refactored/tag_workflow.py

from tag_generator import TagGenerator
from tag_processor import TagProcessor
from services.supabase_service import SupabaseService
from utils.helpers import send_update
import logging

logger = logging.getLogger(__name__)

async def process_tags(video_id, transcript_text, num_tags, clustering_strength, session_id, supabase):
    try:
        logger.info(f"Generating tags for video ID: {video_id}")
        tags = TagGenerator.generate_tags(transcript_text, num_tags=num_tags)

        logger.info(f"Processing tags for video ID: {video_id}")
        final_tags = TagProcessor.process_tags(tags, clustering_strength)

        logger.info(f"Storing tags in Supabase for video ID: {video_id}")
        SupabaseService.insert_tags(supabase, video_id, final_tags)
        SupabaseService.update_video_tags(supabase, video_id, final_tags)

        logger.info(f"Stored {len(final_tags)} tags in Supabase for video ID: {video_id}")

        success = await send_update(session_id, f"Generated and stored {len(final_tags)} tags for video ID: {video_id}", supabase)
        if not success:
            logger.error(f"Failed to send update for video {video_id}")

        return final_tags

    except Exception as e:
        error_message = f"Error processing tags for video ID {video_id}: {str(e)}"
        logger.error(error_message)
        await send_update(session_id, error_message, supabase)
        return []