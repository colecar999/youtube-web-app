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
import openai
import logging
import traceback

from supabase import Client
from utils import send_update

from youtube_transcript_api import YouTubeTranscriptApi  # New import

# Initialize SpaCy model
nlp = spacy.load("en_core_web_sm")

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
SENTENCE_TRANSFORMER_MODEL = os.getenv('SENTENCE_TRANSFORMER_MODEL', 'paraphrase-MiniLM-L6-v2')

# Set up OpenAI API key
openai.api_key = OPENAI_API_KEY

# Lock for status updates
status_lock = Lock()

# Default configuration values
NUM_TAGS_DEFAULT = 5
DISTANCE_THRESHOLD_DEFAULT = 0.3 #delete?
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

async def get_transcript(manager, video_id, session_id, supabase):
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
        await send_update(manager, session_id, f"Transcript for video {video_id} retrieved and stored.", supabase)

        return transcript_data

    except Exception as e:
        error_message = f"Error retrieving transcript for video {video_id}: {str(e)}"
        logger.exception(error_message)  # This will log the full stack trace
        await send_update(manager, session_id, error_message, supabase)
        
        # Store the error status in the database
        error_data = {
            'video_id': video_id,
            'retrieval_date': datetime.now().isoformat(),
            'status': 'failed',
            'source': 'youtube_transcript_api'
        }
        supabase.table('transcripts').insert(error_data).execute()
        
        raise

def generate_tags(transcript_text, num_tags=NUM_TAGS_DEFAULT):
    """
    Generate tags using OpenAI GPT-4.
    """
    prompt = f"Generate {num_tags} relevant tags for the following transcript. The tags are used to describe the content of the transcript.  Provide the tags as a list separated by commas with no numbers.  For example: 'tag1, tag2, tag3, tag4'.  They should be in order of most relevant to least relevant:\\n\\n{transcript_text}"
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
        f" If there are multiple people, their names should be listed and separated by a comma.  For example: 'John Doe, Jane Smith'\\n\\n"
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

async def handle_transcription_status(manager, video_id, existing_transcript, session_id, supabase):
    """
    Handle existing transcription status.
    """
    status = existing_transcript.get('status')
    if status == 'completed':
        await send_update(manager, session_id, f"Existing transcription for video ID: {video_id} found and completed.", supabase)
        return existing_transcript['transcript']
    elif status == 'in_progress':
        await send_update(manager, session_id, f"Existing transcription for video ID: {video_id} is in progress.", supabase)
        # Implement further logic if needed
        return None
    elif status == 'failed':
        await send_update(manager, session_id, f"Previous transcription failed for video ID: {video_id}. Requesting new transcription...", supabase)
        audio_url = await get_audio_url(manager, f"https://www.youtube.com/watch?v={video_id}", session_id, supabase)
        return await get_transcription(manager, audio_url, video_id, session_id, supabase)
    else:
        return None

async def process_video(manager, video, supabase: Client, transcription_ids, session_id, clustering_strength):
    try:
        video_id = video['video_id']
        logger.info(f"Processing video ID: {video_id}")
        
        # Fetch or retrieve transcript
        transcript_data = await get_transcript(manager, video_id, session_id, supabase)

        if transcript_data:
            # Convert transcript data to plain text
            transcript_text = ' '.join([entry['text'] for entry in transcript_data])
            
            # Generate tags using OpenAI
            logger.info(f"Generating tags for video ID: {video_id}")
            tags = generate_tags(transcript_text, num_tags=NUM_TAGS_DEFAULT)
            normalized_tags = [normalize_tag(tag) for tag in tags]
            
            # Detect and separate names from other tags
            names, non_names = detect_names(normalized_tags)
            logger.debug(f"Detected names: {names}")
            logger.debug(f"Non-name tags to be embedded: {non_names}")

            if non_names:
                # Use sentence-transformers to embed the non-name tags
                model = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)
                non_name_embeddings = model.encode(non_names)

                # Use Agglomerative Clustering with user-defined clustering strength
                clustering = AgglomerativeClustering(n_clusters=None, distance_threshold=clustering_strength, affinity='cosine', linkage='average')
                labels = clustering.fit_predict(non_name_embeddings)

                # Create a dictionary to map cluster labels to representative tags
                cluster_to_tag = {}
                for tag, label in zip(non_names, labels):
                    if label not in cluster_to_tag:
                        cluster_to_tag[label] = [tag]
                    else:
                        cluster_to_tag[label].append(tag)

                # Find the most representative tag in each cluster
                consolidated_tags = set()
                tag_mapping = {name: name for name in names}  # Map names to themselves

                for label, tags in cluster_to_tag.items():
                    representative_tag = find_representative_tag(tags, model)
                    for tag in tags:
                        tag_mapping[tag] = representative_tag
                    consolidated_tags.add(representative_tag)
                consolidated_tags.update(names)

                # Map each tag to its cluster representative
                final_tags = [tag_mapping[tag] for tag in normalized_tags]
                final_tags = sorted(set(final_tags))
            else:
                final_tags = sorted(set(normalized_tags))

            # Store tags in Supabase
            logger.info(f"Storing tags in Supabase for video ID: {video_id}")
            for tag in final_tags:
                supabase.table('tags').insert({
                    'video_id': video_id,
                    'tag': tag,
                    'processed_date': datetime.utcnow().isoformat()
                }).execute()
            logger.info(f"Stored {len(final_tags)} tags in Supabase for video ID: {video_id}")

            # Update tags in videos table
            logger.info(f"Updating tags in videos table for video ID: {video_id}")
            supabase.table('videos').update({
                'tags': ", ".join(final_tags),
            }).eq('video_id', video_id).execute()
            logger.info(f"Updated tags in videos table for video ID: {video_id}")

            await send_update(manager, session_id, f"Generated and stored {len(final_tags)} tags for video ID: {video_id}", supabase)

    except Exception as e:
        error_message = f"Error processing video ID {video_id}: {str(e)}"
        logger.error(error_message)
        await send_update(manager, session_id, error_message, supabase)

# Helper function to find representative tag
def find_representative_tag(cluster, model):
    """
    Find the most representative tag in a cluster based on average similarity.
    """
    if len(cluster) == 1:
        return cluster[0]
    
    # Calculate similarity within the cluster
    embeddings = model.encode(cluster)
    similarity_matrix = cosine_similarity(embeddings)
    
    # Find the tag with the highest average similarity to all other tags in the cluster
    avg_similarity = similarity_matrix.mean(axis=1)
    most_representative_index = avg_similarity.argmax()
    return cluster[most_representative_index]

async def process_videos(manager, session_id: str, supabase: Client, video_ids: list, num_videos: int, num_comments: int, num_tags: int, clustering_strength: float):
    """
    Core function to process videos: fetch channel info, videos, comments, transcribe, and generate tags.
    """
    logger.info("Starting process_videos function")
    try:
        await send_update(manager, session_id, "Starting video processing...", supabase)
        
        transcription_ids = load_transcription_ids()
        logger.debug(f"Loaded transcription_ids: {transcription_ids}")

        for video_id in video_ids:
            logger.info(f"Processing video ID: {video_id}")
            try:
                # Step 1: Get channel ID from YouTube API
                logger.debug("Fetching video info from YouTube API")
                video_info_url = 'https://www.googleapis.com/youtube/v3/videos'
                params = {
                    'part': 'snippet',
                    'id': video_id,
                    'key': YOUTUBE_API_KEY
                }
                response = requests.get(video_info_url, params=params)
                response.raise_for_status()
                data = response.json()

                if not data['items']:
                    logger.warning(f"No data found for video ID: {video_id}")
                    await send_update(manager, session_id, f"No data found for video ID: {video_id}", supabase)
                    continue

                snippet = data['items'][0]['snippet']
                channel_id = snippet['channelId']
                channel_title = snippet['channelTitle']
                channel_url = f"https://www.youtube.com/channel/{channel_id}"
                channel_description = snippet.get('description', '')
                logger.info(f"Found channel: {channel_title} (ID: {channel_id})")

                # Step 2: Fetch top videos for the channel
                logger.debug("Fetching top videos for the channel")
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
                top_video_ids = [item['id']['videoId'] for item in search_data['items']]

                # Step 3: Fetch detailed information for these videos
                logger.debug("Fetching detailed information for these videos")
                videos_info_url = 'https://www.googleapis.com/youtube/v3/videos'
                videos_params = {
                    'part': 'snippet,statistics,contentDetails',
                    'id': ','.join(top_video_ids),
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

                # Fetch channel statistics
                logger.debug("Fetching channel statistics")
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
                total_videos = int(channel_stats.get('videoCount', 0))
                subscribers = int(channel_stats.get('subscriberCount', 0))

                # Update the channel information
                logger.debug("Updating the channel information")
                supabase.table('channels').upsert({
                    'channel_id': channel_id,
                    'channel_name': channel_title,
                    'link_to_channel': f"https://www.youtube.com/channel/{channel_id}",
                    'about': snippet.get('description', ''),
                    'number_of_total_videos': total_videos,
                    'number_of_retrieved_videos': len(videos),
                    'ids_of_retrieved_videos': json.dumps(top_video_ids),
                    'subscribers': subscribers,
                    'channel_retrieval_date': datetime.utcnow().isoformat()
                }).execute()

                await send_update(manager, session_id, f"Updated channel info for {channel_title}", supabase)

                supabase.table('videos').upsert(videos).execute()
                await send_update(manager, session_id, f"Saved channel and videos for channel ID: {channel_id}", supabase)

                # Step 5: Fetch and save comments for each video
                logger.debug("Fetching and saving comments for each video")
                comments_url = 'https://www.googleapis.com/youtube/v3/commentThreads'
                for video in videos:
                    comments_params = {
                        'part': 'snippet,replies',  # Add 'replies' to fetch reply comments
                        'videoId': video['video_id'],
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
                            'video_id': video['video_id'],
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
                                    'video_id': video['video_id'],
                                    'comment_id': reply['id'],
                                    'comment_author': reply_snippet.get('authorDisplayName', ''),
                                    'comment_likes': int(reply_snippet.get('likeCount', 0)),
                                    'comment_published_at': reply_snippet.get('publishedAt', ''),
                                    'comment_updated_at': reply_snippet.get('updatedAt', ''),
                                    'comment_parent_id': item['id'],  # Parent comment ID
                                    'comment_text': reply_snippet.get('textOriginal', ''),
                                    'comment_retrieval_date': datetime.utcnow().isoformat()
                                })

                    supabase.table('comments').upsert(comments).execute()
                    await send_update(manager, session_id, f"Saved {len(comments)} comments for video ID: {video['video_id']}", supabase)

                # Step 6: Process each video for transcription and tagging
                logger.info("Starting to process individual videos")
                for video in videos:
                    try:
                        await process_video(manager, video, supabase, transcription_ids, session_id, clustering_strength)
                    except Exception as e:
                        error_message = f"Error processing video ID {video['video_id']}: {str(e)}"
                        logger.error(error_message)
                        await send_update(manager, session_id, error_message, supabase)
                logger.info("Finished processing individual videos")

            except Exception as e:
                error_message = f"Error processing video ID {video_id}: {str(e)}"
                logger.error(error_message)
                await send_update(manager, session_id, error_message, supabase)

        # Save transcription IDs if any new ones were added
        save_transcription_ids(transcription_ids)

        await send_update(manager, session_id, "Video processing completed.", supabase)
    except Exception as e:
        error_message = f"Error in process_videos: {str(e)}"
        logger.error(error_message)
        await send_update(manager, session_id, error_message, supabase)
