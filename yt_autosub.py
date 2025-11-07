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
import yt_dlp
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle

# Load environment variables
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
    return video_id, audio_file


def transcribe_audio(audio_file, groq_api_key):
    """Transcribe audio using Groq Whisper API."""
    print(f"🎤 Transcribing audio with Groq Whisper...")

    client = Groq(api_key=groq_api_key)

    with open(audio_file, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(audio_file, file.read()),
            model="whisper-large-v3-turbo",
            response_format="verbose_json",
            timestamp_granularities=["segment"]
        )

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


def main():
    """Main execution function."""
    if len(sys.argv) < 2:
        print("Usage: python yt_autosub.py <youtube_url>")
        print("Example: python yt_autosub.py https://www.youtube.com/watch?v=VIDEO_ID")
        sys.exit(1)

    video_url = sys.argv[1]

    # Get API key from environment
    groq_api_key = os.getenv('GROQ_API_KEY')
    if not groq_api_key:
        print("❌ Error: GROQ_API_KEY not found in environment")
        print("Please create a .env file with your GROQ_API_KEY")
        sys.exit(1)

    try:
        # Step 1: Download video
        video_id, audio_file = download_video(video_url)

        # Step 2: Transcribe with Groq Whisper
        transcription = transcribe_audio(audio_file, groq_api_key)

        # Step 3: Convert to SRT
        srt_file = f"downloads/{video_id}.srt"
        convert_to_srt(transcription, srt_file)

        # Step 4: Upload to YouTube
        youtube = get_youtube_service()
        upload_subtitles(youtube, video_id, srt_file)

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
