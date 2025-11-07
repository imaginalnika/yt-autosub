#!/usr/bin/env python3
"""
YouTube Auto-Subtitle Generator
Downloads a YouTube video, generates subtitles using Groq Whisper, and uploads them back.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from anthropic import Anthropic
import yt_dlp
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle

# Load environment variables from ~/.env
home_env = Path.home() / '.env'
if home_env.exists():
    load_dotenv(home_env)
else:
    # Fallback to local .env
    load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']


def download_video(video_url, output_dir='downloads'):
    """Download video from YouTube and extract audio."""
    print(f"📥 Downloading video: {video_url}")

    Path(output_dir).mkdir(exist_ok=True)

    # Download video with audio
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': f'{output_dir}/%(id)s.%(ext)s',
        'quiet': False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        video_id = info['id']
        audio_file = f"{output_dir}/{video_id}.mp3"

    print(f"✅ Downloaded audio: {audio_file}")
    return video_id, audio_file, info


def analyze_video_with_claude(video_info, anthropic_api_key):
    """Use Claude to analyze video metadata and generate context for Whisper."""
    print(f"🤖 Analyzing video with Claude...")

    client = Anthropic(api_key=anthropic_api_key)

    # Extract relevant video information
    title = video_info.get('title', 'Unknown')
    description = video_info.get('description', 'No description')
    uploader = video_info.get('uploader', 'Unknown')
    duration = video_info.get('duration', 0)
    tags = video_info.get('tags', [])
    categories = video_info.get('categories', [])

    # Create prompt for Claude
    analysis_prompt = f"""Analyze this YouTube video's metadata and provide:
1. A brief summary of what this video is likely about
2. Key topics or themes
3. Relevant terminology or jargon that might appear in the audio
4. A concise context prompt (2-3 sentences) that will help Whisper transcribe the audio more accurately

Video Title: {title}
Uploader: {uploader}
Duration: {duration} seconds
Tags: {', '.join(tags[:10]) if tags else 'None'}
Categories: {', '.join(categories) if categories else 'None'}
Description: {description[:500]}...

Provide your response in this format:
SUMMARY: [summary]
TOPICS: [topics]
TERMINOLOGY: [terminology]
WHISPER_CONTEXT: [context prompt for whisper]"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": analysis_prompt}
        ]
    )

    analysis = message.content[0].text
    print(f"✅ Claude analysis complete")

    # Extract the Whisper context from Claude's response
    whisper_context = ""
    for line in analysis.split('\n'):
        if line.startswith('WHISPER_CONTEXT:'):
            whisper_context = line.replace('WHISPER_CONTEXT:', '').strip()
            break

    return analysis, whisper_context


def transcribe_audio(audio_file, groq_api_key, prompt=None):
    """Transcribe audio using Groq Whisper API."""
    if prompt:
        print(f"🎤 Transcribing audio with Groq Whisper (with context)...")
        print(f"   Context: {prompt}")
    else:
        print(f"🎤 Transcribing audio with Groq Whisper...")

    client = Groq(api_key=groq_api_key)

    with open(audio_file, "rb") as file:
        # Add prompt parameter if provided (helps with context and accuracy)
        transcription_params = {
            "file": (audio_file, file.read()),
            "model": "whisper-large-v3-turbo",
            "response_format": "verbose_json",
            "timestamp_granularities": ["segment"]
        }

        if prompt:
            transcription_params["prompt"] = prompt

        transcription = client.audio.transcriptions.create(**transcription_params)

    print(f"✅ Transcription complete")
    return transcription


def convert_to_srt(transcription, output_file):
    """Convert transcription to SRT format."""
    print(f"📝 Creating SRT file...")

    with open(output_file, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(transcription.segments, start=1):
            start_time = format_timestamp(segment['start'])
            end_time = format_timestamp(segment['end'])
            text = segment['text'].strip()

            f.write(f"{i}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{text}\n\n")

    print(f"✅ SRT file created: {output_file}")
    return output_file


def format_timestamp(seconds):
    """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def get_youtube_service():
    """Authenticate and return YouTube API service."""
    print("🔐 Authenticating with YouTube...")

    creds = None
    token_file = 'token.pickle'

    # Load existing credentials
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('client_secrets.json'):
                print("❌ Error: client_secrets.json not found!")
                print("Please download OAuth 2.0 credentials from Google Cloud Console")
                print("https://console.cloud.google.com/apis/credentials")
                sys.exit(1)

            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials for next run
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)

    print("✅ YouTube authentication successful")
    return build('youtube', 'v3', credentials=creds)


def upload_subtitles(youtube, video_id, srt_file, language='en'):
    """Upload subtitles to YouTube video."""
    print(f"⬆️  Uploading subtitles to YouTube video: {video_id}")

    try:
        # Insert caption track
        insert_result = youtube.captions().insert(
            part="snippet",
            body=dict(
                snippet=dict(
                    videoId=video_id,
                    language=language,
                    name=f"Auto-generated ({language})",
                    isDraft=False
                )
            ),
            media_body=MediaFileUpload(srt_file, mimetype='application/octet-stream')
        ).execute()

        caption_id = insert_result["id"]
        print(f"✅ Subtitles uploaded successfully! Caption ID: {caption_id}")
        return caption_id

    except Exception as e:
        print(f"❌ Error uploading subtitles: {e}")
        raise


def update_video_description(youtube, video_id, original_url):
    """Update video description to include link to original video."""
    print(f"📝 Updating video description with original link...")

    try:
        # Get current video details
        video_response = youtube.videos().list(
            part="snippet",
            id=video_id
        ).execute()

        if not video_response.get('items'):
            print(f"⚠️  Warning: Could not find video {video_id}")
            return

        video = video_response['items'][0]
        snippet = video['snippet']
        current_description = snippet.get('description', '')

        # Add original video link to description
        attribution_text = f"\n\n---\nOriginal video: {original_url}\nSubtitles generated automatically using Groq Whisper"

        # Check if attribution already exists
        if "Original video:" not in current_description:
            new_description = current_description + attribution_text

            # Update video
            youtube.videos().update(
                part="snippet",
                body={
                    "id": video_id,
                    "snippet": {
                        "title": snippet['title'],
                        "description": new_description,
                        "categoryId": snippet['categoryId']
                    }
                }
            ).execute()

            print(f"✅ Video description updated")
        else:
            print(f"ℹ️  Description already contains attribution")

    except Exception as e:
        print(f"⚠️  Warning: Could not update description: {e}")
        # Don't raise - this is not critical


def main():
    """Main execution function."""
    if len(sys.argv) < 2:
        print("Usage: python yt_autosub.py <youtube_url>")
        print("Example: python yt_autosub.py https://www.youtube.com/watch?v=VIDEO_ID")
        sys.exit(1)

    video_url = sys.argv[1]

    # Get API keys from environment
    groq_api_key = os.getenv('GROQ_API_KEY')
    if not groq_api_key:
        print("❌ Error: GROQ_API_KEY not found in environment")
        print("Please add GROQ_API_KEY to ~/.env")
        sys.exit(1)

    anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
    if not anthropic_api_key:
        print("❌ Error: ANTHROPIC_API_KEY not found in environment")
        print("Please add ANTHROPIC_API_KEY to ~/.env")
        sys.exit(1)

    try:
        # Step 1: Download video
        video_id, audio_file, video_info = download_video(video_url)

        # Step 2: Analyze video with Claude to generate context
        analysis, whisper_context = analyze_video_with_claude(video_info, anthropic_api_key)
        print(f"\n📊 Claude's Analysis:")
        print(analysis)
        print()

        # Step 3: Transcribe with Groq Whisper (with Claude-generated context)
        transcription = transcribe_audio(audio_file, groq_api_key, prompt=whisper_context)

        # Step 4: Convert to SRT
        srt_file = f"downloads/{video_id}.srt"
        convert_to_srt(transcription, srt_file)

        # Step 5: Upload to YouTube
        youtube = get_youtube_service()
        upload_subtitles(youtube, video_id, srt_file)

        # Step 6: Update video description with original link
        update_video_description(youtube, video_id, video_url)

        print("\n🎉 Success! Subtitles have been added to your YouTube video!")
        print(f"   Video: https://www.youtube.com/watch?v={video_id}")

        # Cleanup
        print("\n🧹 Cleaning up temporary files...")
        os.remove(audio_file)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
