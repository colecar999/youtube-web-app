# backend/tasks.py

import os
import re
import sys
import json
import time
import requests
import pandas as pd
from datetime import datetime
from threading import Lock
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import spacy
import yt_dlp
import openai
import assemblyai as aai

from supabase import Client
from main import send_update

# Initialize SpaCy model
nlp = spacy.load("en_core_web_sm")

# Load environment variables
ASSEMBLYAI_API_KEY = os.getenv('ASSEMBLYAI_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
SENTENCE_TRANSFORMER_MODEL = os.getenv('SENTENCE_TRANSFORMER_MODEL', 'paraphrase-MiniLM-L6-v2')

# Set up AssemblyAI and OpenAI API keys
aai.settings.api_key = ASSEMBLYAI_API_KEY
openai.api_key = OPENAI_API_KEY

# Lock for status updates
status_lock = Lock()

# Default configuration values
NUM_TAGS_DEFAULT = 5
DISTANCE_THRESHOLD_DEFAULT = 0.3
MAX_CONCURRENT_REQUESTS = 10  # Adjust based on server capacity

def load_transcription_ids():
    """
    Load transcription IDs from a persistent storage.
    For simplicity, using a JSON file. In production, consider using a database.
    """
    transcription_ids_filename = "transcription_ids.json"
    try:
        with open(transcription_ids_filename, 'r') as file:
            transcription_ids = json.load(file)
            return transcription_ids
    except FileNotFoundError:
        return {}

def save_transcription_ids(transcription_ids):
    """
    Save transcription IDs to a persistent storage.
    """
    transcription_ids_filename = "transcription_ids.json"
    with open(transcription_ids_filename, 'w') as file:
        json.dump(transcription_ids, file, indent=4)

def send_progress_update(supabase: Client, session_id: str, message: str):
    """
    Wrapper to send updates via WebSocket.
    """
    send_update(session_id, message)

def get_audio_url(youtube_url):
    """
    Extract the best audio format URL from YouTube using yt-dlp.
    """
    video_id = youtube_url.split('=')[-1]
    send_update(session_id, f"Extracting audio URL for {video_id} using yt-dlp...")
    with yt_dlp.YoutubeDL() as ydl:
        try:
            info = ydl.extract_info(youtube_url, download=False)
        except Exception as e:
            raise Exception(f"Failed to extract info for {video_id}: {e}")

    for format in info["formats"][::-1]:
        if format.get("vcodec") == "none" and format.get("acodec") == "mp4a.40.2":
            send_update(session_id, f"Selected audio URL for {video_id} found.")
            return format["url"]
    raise Exception(f"No suitable audio format found for {video_id}")

def get_transcription(audio_url, video_id, session_id):
    """
    Get transcription from AssemblyAI with speaker diarization.
    """
    send_update(session_id, f"Requesting transcription for {video_id} from AssemblyAI...")
    transcriber = aai.Transcriber()
    config = aai.TranscriptionConfig(speaker_labels=True)
    retry_count = 0
    max_retries = 3

    while retry_count < max_retries:
        try:
            transcript = transcriber.transcribe(audio_url, config)
            break
        except Exception as e:
            retry_count += 1
            send_update(session_id, f"Retry {retry_count}/{max_retries} for transcription of {video_id} due to error: {e}")
            time.sleep(5)  # Wait before retrying
            if retry_count == max_retries:
                raise Exception(f"Failed to transcribe audio for {video_id} after {max_retries} attempts: {e}")

    transcript_id = transcript.id
    if not transcript_id:
        raise Exception(f"Failed to get transcription ID for {video_id}.")

    headers = {
        "authorization": ASSEMBLYAI_API_KEY,
        "content-type": "application/json"
    }

    send_update(session_id, f"Starting transcription status check loop for {video_id}")

    while True:
        try:
            status_response = requests.get(
                f"<https://api.assemblyai.com/v2/transcript/{transcript_id}>",
                headers=headers
            )
            status_data = status_response.json()
            status = status_data.get('status')

            if status == 'completed':
                send_update(session_id, f"Transcription for {video_id} completed.")
                return transcript.utterances
            elif status == 'failed':
                send_update(session_id, f"Transcription for {video_id} failed.")
                raise Exception(f"Transcription for {video_id} failed. Error: {status_data.get('error', 'Unknown error')}")
            else:
                send_update(session_id, f"Transcription for {video_id} is in progress.")
            time.sleep(15)  # Update status every 15 seconds
        except requests.RequestException as e:
            send_update(session_id, f"Error checking transcription status for {video_id}: {e}")
            time.sleep(15)  # Wait before retrying status check

def generate_tags(transcript_text, num_tags=NUM_TAGS_DEFAULT):
    """
    Generate tags using OpenAI GPT-4.
    """
    prompt = f"Generate {num_tags} relevant tags for the following transcript. Provide the tags as a list separated by commas with no numbers:\\n\\n{transcript_text}"
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    tags = response['choices'][0]['message']['content'].strip().split(',')
    tags = [tag.strip() for tag in tags if tag.strip()]
    return tags

def identify_interviewees(title, description):
    """
    Identify interviewees using OpenAI GPT-3.5 Turbo.
    """
    prompt = (
        f"Based on the following title and description, identify the names of the people being interviewed."
        f" Do not include the host. Do not include any information other than the interviewees."
        f" If there are multiple people, their names should be listed and separated by a comma.\\n\\n"
        f"Title: {title}\\nDescription: {description}"
    )
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    interviewees = response['choices'][0]['message']['content'].strip().split(',')
    interviewees = [person.strip() for person in interviewees if person.strip()]
    return interviewees

def normalize_tag(tag):
    """
    Normalize a tag string.
    """
    tag = tag.strip().lower()
    tag = re.sub(r'[^a-z0-9\\s]', '', tag)  # Remove special characters
    tag = re.sub(r'\\s+', ' ', tag)  # Replace multiple spaces with single space
    return tag

def detect_names(tags):
    """
    Detect names in the tags and separate them from other tags.
    """
    names = []
    non_names = []
    for tag in tags:
        doc = nlp(tag)
        if any(ent.label_ == "PERSON" for ent in doc.ents):
            names.append(tag)
        else:
            non_names.append(tag)
    return names, non_names

def handle_transcription_status(video_id, existing_transcript, session_id):
    """
    Handle existing transcription status.
    """
    status = existing_transcript.get('status')
    if status == 'completed':
        send_update(session_id, f"Existing transcription for video ID: {video_id} found and completed.")
        return existing_transcript['transcript']
    elif status == 'in_progress':
        send_update(session_id, f"Existing transcription for video ID: {video_id} is in progress.")
        # Implement further logic if needed
        return None
    elif status == 'failed':
        send_update(session_id, f"Previous transcription failed for video ID: {video_id}. Requesting new transcription...")
        audio_url = get_audio_url(f"<https://www.youtube.com/watch?v={video_id}>")
        return get_transcription(audio_url, video_id, session_id)
    else:
        return None

def process_video(row, supabase: Client, transcription_ids, session_id):
    """
    Process each video: extract audio URL, get transcription and tags, and identify interviewees.
    """
    video_id = row['video_id']
    channel_name = row['channel_name'].replace(" ", "_")
    video_title = row['title'].replace(" ", "_")
    description = row['description']
    youtube_url = f"<https://www.youtube.com/watch?v={video_id}>"
    send_update(session_id, f"Processing video ID: {video_id}")

    filename = f"{video_id}_{channel_name}_{video_title}_transcript.json"
    # Placeholder for saving or loading transcripts if needed

    existing_transcript = supabase.table('transcripts').select('*').eq('video_id', video_id).single().execute()

    if existing_transcript.data:
        send_update(session_id, f"Found existing transcript for video ID: {video_id}")
        if existing_transcript.data['status'] == 'completed':
            transcript_text = existing_transcript.data['transcript']
        elif existing_transcript.data['status'] == 'in_progress':
            transcript_text = handle_transcription_status(video_id, existing_transcript.data, session_id)
        elif existing_transcript.data['status'] == 'failed':
            transcript_text = handle_transcription_status(video_id, existing_transcript.data, session_id)
    else:
        try:
            audio_url = get_audio_url(youtube_url)
            transcript_utterances = get_transcription(audio_url, video_id, session_id)
            transcript_text = " ".join([utterance['text'] for utterance in transcript_utterances])

            # Save transcription to Supabase
            supabase.table('transcripts').insert({
                'video_id': video_id,
                'transcript': transcript_text,
                'retrieval_date': datetime.utcnow().isoformat(),
                'status': 'completed'
            }).execute()

        except Exception as e:
            send_update(session_id, f"Error processing video {video_id}: {e}")
            return

    if transcript_text:
        # Generate tags
        tags = generate_tags(transcript_text)
        normalized_tags = [normalize_tag(tag) for tag in tags]
        interviewees = identify_interviewees(video_title, description)

        # Detect names
        names, non_names = detect_names(normalized_tags)

        # Store tags in Supabase
        for tag in normalized_tags:
            supabase.table('tags').insert({
                'video_id': video_id,
                'tag': tag,
                'processed_date': datetime.utcnow().isoformat()
            }).execute()

        # Update tags in videos table
        supabase.table('videos').update({
            'tags': ", ".join(normalized_tags),
            'interviewees': ", ".join(interviewees)
        }).eq('video_id', video_id).execute()

        send_update(session_id, f"Generated tags and identified interviewees for video ID: {video_id}")

def process_videos(session_id: str, supabase: Client, video_ids: list, num_videos: int, num_comments: int, num_tags: int, clustering_strength: float):
    """
    Core function to process videos: fetch channel info, videos, comments, transcribe, and generate tags.
    """
    send_update(session_id, "Starting video processing...")

    transcription_ids = load_transcription_ids()

    for video_id in video_ids:
        try:
            # Step 1: Get channel ID from YouTube API
            video_info_url = '<https://www.googleapis.com/youtube/v3/videos>'
            params = {
                'part': 'snippet',
                'id': video_id,
                'key': YOUTUBE_API_KEY
            }
            response = requests.get(video_info_url, params=params)
            if response.status_code != 200:
                send_update(session_id, f"Failed to retrieve video info for {video_id}: {response.text}")
                continue

            data = response.json()
            if not data['items']:
                send_update(session_id, f"No data found for video ID: {video_id}")
                continue

            snippet = data['items'][0]['snippet']
            channel_id = snippet['channelId']
            channel_title = snippet['channelTitle']
            channel_url = f"<https://www.youtube.com/channel/{channel_id}>"
            channel_description = snippet.get('description', '')
            subscribers = 0  # YouTube API requires additional calls to get subscriber count

            # Step 2: Fetch top videos for the channel
            search_url = '<https://www.googleapis.com/youtube/v3/search>'
            search_params = {
                'part': 'id',
                'channelId': channel_id,
                'maxResults': num_videos,
                'order': 'viewCount',
                'type': 'video',
                'key': YOUTUBE_API_KEY
            }
            search_response = requests.get(search_url, params=search_params)
            if search_response.status_code != 200:
                send_update(session_id, f"Failed to retrieve top videos for channel {channel_id}: {search_response.text}")
                continue

            search_data = search_response.json()
            top_video_ids = [item['id']['videoId'] for item in search_data['items']]

            # Step 3: Fetch detailed information for these videos
            videos_info_url = '<https://www.googleapis.com/youtube/v3/videos>'
            videos_params = {
                'part': 'snippet,statistics,contentDetails',
                'id': ','.join(top_video_ids),
                'key': YOUTUBE_API_KEY
            }
            videos_response = requests.get(videos_info_url, params=videos_params)
            if videos_response.status_code != 200:
                send_update(session_id, f"Failed to retrieve video details for channel {channel_id}: {videos_response.text}")
                continue

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

            # Step 4: Save channel and videos to Supabase
            supabase.table('channels').upsert({
                'channel_id': channel_id,
                'channel_name': channel_title,
                'link_to_channel': channel_url,
                'about': channel_description,
                'number_of_total_videos': 0,  # Requires additional API calls
                'number_of_retrieved_videos': len(videos),
                'ids_of_retrieved_videos': json.dumps(top_video_ids),
                'subscribers': subscribers,
                'channel_retrieval_date': datetime.utcnow().isoformat()
            }).execute()

            supabase.table('videos').upsert(videos).execute()
            send_update(session_id, f"Saved channel and videos for channel ID: {channel_id}")

            # Step 5: Fetch and save comments for each video
            comments_url = '<https://www.googleapis.com/youtube/v3/commentThreads>'
            for video in videos:
                comments_params = {
                    'part': 'snippet',
                    'videoId': video['video_id'],
                    'maxResults': num_comments,
                    'order': 'relevance',
                    'key': YOUTUBE_API_KEY
                }
                comments_response = requests.get(comments_url, params=comments_params)
                if comments_response.status_code != 200:
                    send_update(session_id, f"Failed to retrieve comments for video {video['video_id']}: {comments_response.text}")
                    continue

                comments_data = comments_response.json()
                comments = []
                for item in comments_data['items']:
                    comment = item['snippet']['topLevelComment']['snippet']
                    comments.append({
                        'video_id': video['video_id'],
                        'comment_id': item['id'],
                        'comment_author': comment.get('authorDisplayName', ''),
                        'comment_likes': int(comment.get('likeCount', 0)),
                        'comment_published_at': comment.get('publishedAt', ''),
                        'comment_updated_at': comment.get('updatedAt', ''),
                        'comment_parent_id': '',  # No parent ID for top-level comments
                        'comment_text': comment.get('textOriginal', ''),
                        'comment_retrieval_date': datetime.utcnow().isoformat()
                    })

                supabase.table('comments').upsert(comments).execute()
                send_update(session_id, f"Saved comments for video ID: {video['video_id']}")

            # Step 6: Process each video for transcription and tagging
            for video in videos:
                process_video(video, supabase, transcription_ids, session_id)

        except Exception as e:
            send_update(session_id, f"Error processing video ID {video_id}: {e}")

    # Save transcription IDs if any new ones were added
    save_transcription_ids(transcription_ids)

    send_update(session_id, "Video processing completed.")
