# YouTube Auto-Subtitle Generator

Automatically download YouTube videos, generate subtitles using Groq Whisper AI, and upload them back to YouTube.

## Features

- Downloads audio from YouTube videos
- Transcribes audio using Groq's Whisper API
- Generates SRT subtitle files
- Automatically uploads subtitles to YouTube

## Prerequisites

- Python 3.7+
- Groq API key ([Get one here](https://console.groq.com/keys))
- Google Cloud Project with YouTube Data API v3 enabled
- YouTube OAuth credentials

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Groq API Key

1. Go to [Groq Console](https://console.groq.com/keys)
2. Create an account or sign in
3. Generate a new API key
4. Copy the API key

### 3. Set up YouTube API Access

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **YouTube Data API v3**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "YouTube Data API v3"
   - Click "Enable"
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as the application type
   - Download the credentials as `client_secrets.json`
   - Place `client_secrets.json` in the project root directory

### 4. Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your Groq API key:
   ```
   GROQ_API_KEY=your_actual_api_key_here
   ```

## Usage

Run the script with a YouTube URL:

```bash
python yt_autosub.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

### First Run

On your first run, the script will:
1. Open your browser for YouTube authentication
2. Ask you to sign in with your Google account
3. Request permission to manage your YouTube videos
4. Save authentication token for future runs

### What Happens

1. **Download**: The script downloads the audio from the YouTube video
2. **Transcribe**: Sends audio to Groq Whisper for transcription
3. **Convert**: Creates an SRT subtitle file
4. **Upload**: Uploads subtitles to your YouTube video
5. **Cleanup**: Removes temporary audio files

## Example

```bash
python yt_autosub.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

Output:
```
📥 Downloading video: https://www.youtube.com/watch?v=dQw4w9WgXcQ
✅ Downloaded audio: downloads/dQw4w9WgXcQ.mp3
🎤 Transcribing audio with Groq Whisper...
✅ Transcription complete
📝 Creating SRT file...
✅ SRT file created: downloads/dQw4w9WgXcQ.srt
🔐 Authenticating with YouTube...
✅ YouTube authentication successful
⬆️  Uploading subtitles to YouTube video: dQw4w9WgXcQ
✅ Subtitles uploaded successfully!

🎉 Success! Subtitles have been added to your YouTube video!
```

## Files

- `yt_autosub.py` - Main script
- `requirements.txt` - Python dependencies
- `.env` - Your API keys (create from .env.example)
- `client_secrets.json` - YouTube OAuth credentials (download from Google Cloud)
- `token.pickle` - Saved YouTube authentication (auto-generated)
- `downloads/` - Temporary files directory (auto-generated)

## Notes

- The script only works with videos you own or have permission to edit
- Subtitles are uploaded in English by default
- Audio files are automatically deleted after processing
- The authentication token is saved for future runs

## Troubleshooting

**"GROQ_API_KEY not found"**
- Make sure you've created a `.env` file with your API key

**"client_secrets.json not found"**
- Download OAuth credentials from Google Cloud Console
- Make sure the file is named `client_secrets.json` and in the project root

**"Permission denied" when uploading subtitles**
- Ensure you're authenticated with the YouTube account that owns the video
- Delete `token.pickle` and re-authenticate

**YouTube API quota exceeded**
- YouTube API has daily quotas; wait until the next day or request a quota increase

## License

MIT
