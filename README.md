# YouTube Auto-Subtitle Generator

Automatically download YouTube videos, generate subtitles using Groq Whisper AI with Claude-powered context analysis, and upload them back to YouTube.

## Features

- Downloads audio from YouTube videos
- Uses Claude AI to analyze video metadata and generate intelligent context
- Transcribes audio using Groq's Whisper API with context-aware prompts for better accuracy
- Generates SRT subtitle files
- Automatically uploads subtitles to YouTube
- Updates video description with link to original video

## Prerequisites

- Python 3.7+
- Groq API key ([Get one here](https://console.groq.com/keys))
- Anthropic API key ([Get one here](https://console.anthropic.com/))
- Google Cloud Project with YouTube Data API v3 enabled
- YouTube OAuth credentials

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get API Keys

#### Groq API Key (for Whisper transcription)

1. Go to [Groq Console](https://console.groq.com/keys)
2. Create an account or sign in
3. Generate a new API key
4. Copy the API key

#### Anthropic API Key (for Claude video analysis)

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Create an account or sign in
3. Navigate to API Keys
4. Generate a new API key
5. Copy the API key

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

The script reads API keys from `~/.env` (your home directory). You can also use a local `.env` file as a fallback.

1. Create or edit `~/.env` in your home directory:
   ```bash
   nano ~/.env
   ```

2. Add your API keys:
   ```
   GROQ_API_KEY=your_actual_groq_api_key_here
   ANTHROPIC_API_KEY=your_actual_anthropic_api_key_here
   ```

3. Save and close the file

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

1. **Download**: The script downloads the audio from the YouTube video and extracts metadata
2. **Analyze**: Claude analyzes the video metadata (title, description, tags) to understand the context
3. **Generate Context**: Claude creates an intelligent prompt to help Whisper understand domain-specific terms
4. **Transcribe**: Sends audio to Groq Whisper with the Claude-generated context for better accuracy
5. **Convert**: Creates an SRT subtitle file
6. **Upload**: Uploads subtitles to your YouTube video
7. **Update Description**: Adds a link to the original video in the description
8. **Cleanup**: Removes temporary audio files

## Example

```bash
python yt_autosub.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

Output:
```
📥 Downloading video: https://www.youtube.com/watch?v=dQw4w9WgXcQ
✅ Downloaded audio: downloads/dQw4w9WgXcQ.mp3
🤖 Analyzing video with Claude...
✅ Claude analysis complete

📊 Claude's Analysis:
SUMMARY: Music video featuring a popular 1980s song
TOPICS: Music, entertainment, pop culture
TERMINOLOGY: Musical terms, performance, choreography
WHISPER_CONTEXT: This is a music video from the 1980s featuring vocals and instrumental performance.

🎤 Transcribing audio with Groq Whisper (with context)...
   Context: This is a music video from the 1980s featuring vocals and instrumental performance.
✅ Transcription complete
📝 Creating SRT file...
✅ SRT file created: downloads/dQw4w9WgXcQ.srt
🔐 Authenticating with YouTube...
✅ YouTube authentication successful
⬆️  Uploading subtitles to YouTube video: dQw4w9WgXcQ
✅ Subtitles uploaded successfully!
📝 Updating video description with original link...
✅ Video description updated

🎉 Success! Subtitles have been added to your YouTube video!
   Video: https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

## Files

- `yt_autosub.py` - Main script
- `requirements.txt` - Python dependencies
- `~/.env` - Your API keys in home directory (or local `.env` as fallback)
- `client_secrets.json` - YouTube OAuth credentials (download from Google Cloud)
- `token.pickle` - Saved YouTube authentication (auto-generated)
- `downloads/` - Temporary files directory (auto-generated)

## Notes

- The script reads API keys from `~/.env` in your home directory (falls back to local `.env`)
- The script only works with videos you own or have permission to edit
- Subtitles are uploaded in English by default
- Audio files are automatically deleted after processing
- The authentication token is saved for future runs
- Claude analyzes video metadata to provide context for better transcription accuracy
- The video description is automatically updated with a link to the original video

## Troubleshooting

**"GROQ_API_KEY not found" or "ANTHROPIC_API_KEY not found"**
- Make sure you've created `~/.env` in your home directory with both API keys
- Alternatively, create a local `.env` file in the project directory

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
