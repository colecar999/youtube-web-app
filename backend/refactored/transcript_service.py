# backend/services/transcript_service.py

import json
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi
from utils.helpers import send_update

class TranscriptService:
    @staticmethod
    async def get_transcript(video_id, session_id, supabase):
        try:
            # Fetch the transcript
            transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
            
            # Prepare the data for storage
            transcript_json = json.dumps(transcript_data)
            retrieval_date = datetime.now().isoformat()
            source = 'youtube_transcript_api'
            status = 'completed'

            # Store in the database
            data = {
                'video_id': video_id,
                'transcript': transcript_json,
                'retrieval_date': retrieval_date,
                'status': status,
                'source': source
            }
            
            # Assuming you have a 'transcripts' table in Supabase
            result = supabase.table('transcripts').insert(data).execute()

            # Send update
            success = await send_update(session_id, f"Transcript for video {video_id} retrieved and stored.", supabase)
            if not success:
                print(f"Failed to send update for video {video_id}")

            return transcript_data

        except Exception as e:
            error_message = f"Error retrieving transcript for video {video_id}: {str(e)}"
            print(error_message)  # This will log the full stack trace
            success = await send_update(session_id, error_message, supabase)
            if not success:
                print(f"Failed to send error update for video {video_id}")
            
            # Store the error status in the database
            error_data = {
                'video_id': video_id,
                'retrieval_date': datetime.now().isoformat(),
                'status': 'failed',
                'source': 'youtube_transcript_api'
            }
            supabase.table('transcripts').insert(error_data).execute()
            
            raise

    @staticmethod
    async def handle_transcription_status(video_id, existing_transcript, session_id, supabase):
        """
        Handle existing transcription status.
        """
        status = existing_transcript.get('status')
        if status == 'completed':
            success = await send_update(session_id, f"Existing transcription for video ID: {video_id} found and completed.", supabase)
            if not success:
                print(f"Failed to send update for video {video_id}")
            return existing_transcript['transcript']
        elif status == 'in_progress':
            success = await send_update(session_id, f"Existing transcription for video ID: {video_id} is in progress.", supabase)
            if not success:
                print(f"Failed to send update for video {video_id}")
            # Implement further logic if needed
            return None
        elif status == 'failed':
            success = await send_update(session_id, f"Previous transcription failed for video ID: {video_id}. Requesting new transcription...", supabase)
            if not success:
                print(f"Failed to send update for video {video_id}")
            return await TranscriptService.get_transcript(video_id, session_id, supabase)
        else:
            return None