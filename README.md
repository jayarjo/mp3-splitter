# YouTube MP3 Splitter

A Python script to download YouTube videos as MP3 and split them into separate tracks based on timestamps.

## Features

- Download YouTube videos as high-quality MP3 using yt-dlp
- Split audio into multiple tracks based on timestamp file
- Support multiple timestamp formats
- Automatic track numbering
- Clean, sanitized filenames
- **Memory-efficient processing** - handles large files (tested with 3.36GB, 38+ hours)
- Smart caching - skip re-downloading existing files
- **Resume capability** - automatically skips already processed tracks if interrupted
- Optimized for long-form content (audiobooks, podcasts, lectures)
- **Real-time progress bar** with ETA, current track, and statistics

## Quick Start with Docker (Recommended)

The easiest way to use this tool is with Docker - no need to install Python, ffmpeg, or any dependencies on your host machine!

### Requirements
- Docker (https://docs.docker.com/get-docker/)
- Make (optional but recommended)

### Easiest: Using Makefile (Linux/macOS)

```bash
# Build the Docker image
make build

# Split a YouTube video (natural syntax!)
make run "https://youtube.com/watch?v=..." timestamps.txt

# With standard command-line flags
make run "https://youtube.com/..." timestamps.txt --force-download
make run "https://youtube.com/..." timestamps.txt -o my_chapters
make run "https://youtube.com/..." timestamps.txt --keep-original -o audiobook

# See all available commands
make help

# Clean up output files
make clean
```

**Quick reference:**
- `make build` or `make b` - Build Docker image
- `make run` or `make r` or `make s` - Run the splitter with any arguments
- `make clean` or `make c` - Clean output directories
- `make help` or `make h` - Show all commands

### Alternative: Using Shell Scripts

**Linux/macOS:**
```bash
./run.sh "YOUTUBE_URL" timestamps.txt
```

**Windows:**
```bash
run.bat "YOUTUBE_URL" timestamps.txt
```

The first run will automatically build the Docker image. Subsequent runs will be faster.

### Advanced: Docker Commands

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

**Force re-download with Docker:**
```bash
./run.sh "YOUTUBE_URL" timestamps.txt --force-download
```

**Note:** Downloaded files are saved to `./downloads/` on your host machine. If a file already exists, it will be reused automatically (skipping the download). This is useful for re-splitting with different timestamps. Use `--force-download` to override.

## Makefile Commands Reference

The Makefile provides convenient shortcuts with **natural command-line syntax**:

| Command | Shortcut | Description |
|---------|----------|-------------|
| `make help` | `make h` | Show all available commands with descriptions |
| `make build` | `make b` | Build the Docker image |
| `make rebuild` | - | Rebuild image from scratch (no cache) |
| `make run` | `make r`, `make s` | Run the splitter (accepts all standard arguments) |
| `make clean` | `make c` | Clean output and downloads directories |
| `make clean-all` | - | Clean everything including Docker image |
| `make shell` | - | Open bash shell in container for debugging |
| `make version` | - | Show version information |

**Natural Syntax - Just Like the Command Line:**

The Makefile now accepts arguments exactly like you'd use them with the script itself!

```bash
# Basic usage
make run "https://youtube.com/watch?v=..." timestamps_audiobook.txt

# With standard flags (just like the CLI!)
make run "https://youtube.com/..." timestamps.txt --force-download
make run "https://youtube.com/..." timestamps.txt -o my_chapters
make run "https://youtube.com/..." timestamps.txt --keep-original
make run "https://youtube.com/..." timestamps.txt -o audiobook -d temp --force-download

# Even shorter with aliases
make r "https://youtube.com/..." timestamps.txt
make s "https://youtube.com/..." timestamps.txt --force-download

# Debug: Open shell in container
make shell
```

**All standard script options work:**
- `-o, --output DIR` - Custom output directory
- `-d, --download-dir DIR` - Custom download directory
- `--keep-original` - Keep the original downloaded file
- `--force-download` - Force re-download even if file exists

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

### Force re-download existing file:
```bash
python youtube_mp3_splitter.py --force-download "YOUTUBE_URL" timestamps.txt
```

### Full options:
```bash
python youtube_mp3_splitter.py [-h] [-o OUTPUT] [-d DOWNLOAD_DIR] [--keep-original] [--force-download] url timestamps
```

**Options:**
- `-o, --output`: Output directory for split files (default: output)
- `-d, --download-dir`: Directory for downloaded MP3 (default: downloads)
- `--keep-original`: Keep the original downloaded MP3 file
- `--force-download`: Force re-download even if file already exists
- `-h, --help`: Show help message

**Note:** The script automatically skips downloading if the MP3 file already exists in the download directory. This saves time and bandwidth when re-splitting with different timestamps. Use `--force-download` to override this behavior.

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

### Format 3: Long-form content (audiobooks, podcasts)
```
1:05 Chapter 1 Crimson
12:49 Chapter 2 Situation
1:01:18 Chapter 3 The Long Chapter
2:15:30 Chapter 4 Final Chapter
```

**Supported time formats:**
- `HH:MM:SS` (hours:minutes:seconds) - e.g., `1:23:45`
- `MM:SS` (minutes:seconds) - e.g., `12:49`
- `M:SS` (minutes:seconds) - e.g., `1:05`
- `SS` (seconds) - e.g., `45`

**Notes:**
- Lines starting with `#` are treated as comments
- Empty lines are ignored
- Track names will be sanitized for safe filenames
- Output files are numbered (01, 02, 03, etc.)
- The last track automatically extends to the end of the audio

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

## Performance & Large Files

The script automatically optimizes for file size:

- **Small files (<500MB)**: Uses pydub for processing
- **Large files (≥500MB)**: Automatically switches to memory-efficient ffmpeg mode

### Large File Support

Tested with very large audiobooks:
- **File size**: 3.36GB
- **Duration**: 38+ hours
- **Tracks**: 170 chapters
- **Processing**: Uses direct ffmpeg streaming (no memory loading)

**Benefits for large files:**
- Minimal memory usage (doesn't load entire file)
- Fast processing with progress indicators
- Handles multi-hour content efficiently
- Shows file sizes in GB for clarity

**Example output for large files:**
```
Large file detected (3445.2 MB). Using memory-efficient ffmpeg mode.

Preparing to split audio file: downloads/audiobook.mp3
File size: 3.36 GB
Getting audio duration...
Total duration: 38:24:15 (138255.0 seconds)

Splitting into 170 tracks using ffmpeg (memory-efficient mode)...

⏳ [001/170] Processing: Chapter 1 Crimson
   ✓ Saved: 001 - Chapter 1 Crimson.mp3 (10.2 MB) | ETA: 21:15

⏳ [002/170] Processing: Chapter 2 Situation
   ✓ Saved: 002 - Chapter 2 Situation.mp3 (13.7 MB) | ETA: 21:03

⏳ [003/170] Processing: Chapter 3 Melissa
   ✓ Saved: 003 - Chapter 3 Melissa.mp3 (11.8 MB) | ETA: 20:48
...

Overall Progress:  2%|█░░░░░░░░░░░░░░░░░| 3/170 [00:45<21:30, 0.13track/s]

============================================================
✓ Successfully split 170 tracks!
  Total output size: 1854.3 MB (1.81 GB)
  Total time: 22:35
  Average time per track: 7.9s
  Output directory: output
============================================================
```

**Progress Bar Features:**
- Real-time progress bar on stable line (doesn't jump around)
- Current track being processed shown above progress bar
- ETA (estimated time remaining) calculated after each track
- Individual track completion with file size
- Final summary with total statistics

## Resume Capability

The script automatically resumes if interrupted! If the process stops for any reason (power failure, Ctrl+C, network issues), simply run the same command again.

**Graceful Interruption:**
- Press **Ctrl+C** at any time to stop processing
- Script will exit gracefully with a helpful message
- Shows which track was being processed when interrupted
- Reminds you that you can resume by rerunning the same command

**How it works:**
- Before processing each track, checks if output file already exists
- If file exists and is valid (>100KB), automatically skips it
- Continues with remaining unprocessed tracks
- If file exists but is suspiciously small (<100KB), re-processes it (likely corrupted)

**Example of graceful interruption (Ctrl+C):**
```
⏳ [042/170] Processing: Chapter 42 Mysticism
^C

============================================================
⚠️  Interrupted by user (Ctrl+C)
============================================================

Currently processing: [042/170] Chapter 42 Mysticism
⚠️  Note: This track may be incomplete or corrupted.

💡 You can resume by running the same command again.
   Already completed tracks will be automatically skipped.

Exiting gracefully...
```

**Example resumed session:**
```
⏭️  [001/170] Skipping (already exists): 001 - Chapter 1 Crimson.mp3 (10.2 MB)
⏭️  [002/170] Skipping (already exists): 002 - Chapter 2 Situation.mp3 (13.7 MB)
...
⏭️  [041/170] Skipping (already exists): 041 - Chapter 41 Findings.mp3 (11.3 MB)

⏳ [042/170] Processing: Chapter 42 Mysticism
   ✓ Saved: 042 - Chapter 42 Mysticism.mp3 (12.1 MB) | ETA: 18:32
...

============================================================
✓ Complete!
  Total tracks: 170
  Processed: 167 | Skipped: 3 (already existed)
  Total output size: 1854.3 MB (1.81 GB)
  Processing time: 18:42
  Average time per track: 6.7s
  Output directory: output
============================================================
```

**Benefits:**
- Safe to interrupt at any time (Ctrl+C)
- No wasted processing if something goes wrong
- Perfect for very large jobs (100+ chapters)
- Automatic corruption detection (re-processes tiny files)

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
