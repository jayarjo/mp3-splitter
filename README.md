# YouTube MP3 Splitter

A Python script to download YouTube videos as MP3 and split them into separate tracks based on timestamps.

## Features

- Download YouTube videos as high-quality MP3 using yt-dlp
- Split audio into multiple tracks based on timestamp file
- Support multiple timestamp formats
- Automatic track numbering
- Clean, sanitized filenames

## Quick Start with Docker (Recommended)

The easiest way to use this tool is with Docker - no need to install Python, ffmpeg, or any dependencies on your host machine!

### Requirements
- Docker (https://docs.docker.com/get-docker/)

### Usage

**Linux/macOS:**
```bash
./run.sh "YOUTUBE_URL" timestamps.txt
```

**Windows:**
```bash
run.bat "YOUTUBE_URL" timestamps.txt
```

The first run will automatically build the Docker image. Subsequent runs will be faster.

### Docker Commands

**Build the image manually:**
```bash
docker build -t youtube-mp3-splitter:latest .
```

**Run with Docker directly:**
```bash
docker run --rm \
  -v "$(pwd):/data" \
  -v "$(pwd)/output:/app/output" \
  -v "$(pwd)/downloads:/app/downloads" \
  -w /data \
  youtube-mp3-splitter:latest "YOUTUBE_URL" timestamps.txt
```

**Using docker-compose:**
```bash
docker-compose run --rm mp3-splitter "YOUTUBE_URL" timestamps.txt
```

## Manual Installation (Alternative)

If you prefer not to use Docker, you can install everything manually:

### Requirements

- Python 3.7+
- ffmpeg (required by yt-dlp and pydub)

### Installing ffmpeg

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html

### Installation Steps

1. Clone or download this repository

2. Create a virtual environment:
```bash
python3 -m venv venv
```

3. Activate the virtual environment:

**Linux/macOS:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

## Manual Usage

### Basic usage:
```bash
python youtube_mp3_splitter.py "YOUTUBE_URL" timestamps.txt
```

### With custom output directory:
```bash
python youtube_mp3_splitter.py -o my_tracks "YOUTUBE_URL" timestamps.txt
```

### Keep original downloaded file:
```bash
python youtube_mp3_splitter.py --keep-original "YOUTUBE_URL" timestamps.txt
```

### Full options:
```bash
python youtube_mp3_splitter.py [-h] [-o OUTPUT] [-d DOWNLOAD_DIR] [--keep-original] url timestamps
```

**Options:**
- `-o, --output`: Output directory for split files (default: output)
- `-d, --download-dir`: Directory for downloaded MP3 (default: downloads)
- `--keep-original`: Keep the original downloaded MP3 file
- `-h, --help`: Show help message

## Timestamps File Format

The script supports two timestamp formats:

### Format 1: Explicit start and end times
```
00:00 - 03:45 First Track
03:45 - 07:30 Second Track
07:30 - 12:00 Third Track
```

### Format 2: Start time only (end inferred from next track)
```
00:00 First Track
03:45 Second Track
07:30 Third Track
```

**Supported time formats:**
- `HH:MM:SS` (hours:minutes:seconds)
- `MM:SS` (minutes:seconds)
- `SS` (seconds)

**Notes:**
- Lines starting with `#` are treated as comments
- Empty lines are ignored
- Track names will be sanitized for safe filenames
- Output files are numbered (01, 02, 03, etc.)

## Example

1. Create a timestamps file `my_timestamps.txt`:
```
00:00 Introduction
02:30 Chapter 1 - Getting Started
10:15 Chapter 2 - Advanced Topics
18:45 Conclusion
```

2. Run the script:
```bash
python youtube_mp3_splitter.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" my_timestamps.txt
```

3. Find your split tracks in the `output/` directory:
```
01 - Introduction.mp3
02 - Chapter 1 - Getting Started.mp3
03 - Chapter 2 - Advanced Topics.mp3
04 - Conclusion.mp3
```

## Output

The script will:
1. Download the YouTube video as MP3 to the `downloads/` directory
2. Split it into separate tracks in the `output/` directory
3. Delete the original downloaded file (unless `--keep-original` is used)

## Troubleshooting

**Error: ffmpeg not found**
- Make sure ffmpeg is installed and available in your PATH

**Error: No valid timestamps found**
- Check your timestamps file format
- Ensure times are in the correct format (HH:MM:SS, MM:SS, or SS)

**Download errors**
- Try updating yt-dlp: `pip install --upgrade yt-dlp`
- Some videos may be restricted or unavailable

## License

MIT License - Feel free to use and modify as needed.
