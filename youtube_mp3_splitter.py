#!/usr/bin/env python3
"""
YouTube MP3 Splitter
Downloads a YouTube video as MP3 and splits it into separate files based on timestamps.
"""

import argparse
import os
import sys
import re
import subprocess
import shutil
import time
from pathlib import Path
from typing import List, Tuple
import yt_dlp
from pydub import AudioSegment
from tqdm import tqdm


def check_ffmpeg():
    """Check if ffmpeg is available."""
    if not shutil.which('ffmpeg'):
        print("❌ Error: ffmpeg is not installed or not in PATH", file=sys.stderr)
        print("ffmpeg is required for audio processing.", file=sys.stderr)
        print("\nInstallation instructions:", file=sys.stderr)
        print("  Ubuntu/Debian: sudo apt install ffmpeg", file=sys.stderr)
        print("  macOS: brew install ffmpeg", file=sys.stderr)
        print("  Windows: Download from https://ffmpeg.org/download.html", file=sys.stderr)
        return False
    return True


def parse_timestamp(timestamp: str) -> int:
    """
    Convert timestamp string to milliseconds.
    Supports formats: HH:MM:SS, MM:SS, SS

    Args:
        timestamp: Time string (e.g., "1:23:45", "5:30", "45")

    Returns:
        Time in milliseconds
    """
    parts = timestamp.strip().split(':')
    parts.reverse()

    seconds = 0
    multipliers = [1, 60, 3600]  # seconds, minutes, hours

    for i, part in enumerate(parts):
        if i < len(multipliers):
            seconds += int(part) * multipliers[i]

    return seconds * 1000  # Convert to milliseconds


def parse_timestamps_file(filepath: str) -> List[Tuple[int, int, str]]:
    """
    Parse timestamps file.
    Expected format (one per line):
        00:00 - 03:45 Track Name
        03:45 - 07:30 Another Track
    or:
        00:00 Track Name
        03:45 Another Track

    Args:
        filepath: Path to timestamps file

    Returns:
        List of tuples: (start_ms, end_ms, track_name)
    """
    timestamps = []

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

    for i, line in enumerate(lines):
        # Try format: "00:00 - 03:45 Track Name"
        match = re.match(r'^([\d:]+)\s*-\s*([\d:]+)\s+(.+)$', line)
        if match:
            start_time = parse_timestamp(match.group(1))
            end_time = parse_timestamp(match.group(2))
            track_name = match.group(3).strip()
            timestamps.append((start_time, end_time, track_name))
            continue

        # Try format: "00:00 Track Name"
        match = re.match(r'^([\d:]+)\s+(.+)$', line)
        if match:
            start_time = parse_timestamp(match.group(1))
            track_name = match.group(2).strip()

            # End time is the start of the next track, or None for the last track
            if i + 1 < len(lines):
                next_match = re.match(r'^([\d:]+)', lines[i + 1])
                if next_match:
                    end_time = parse_timestamp(next_match.group(1))
                else:
                    end_time = None
            else:
                end_time = None

            timestamps.append((start_time, end_time, track_name))
            continue

        print(f"Warning: Could not parse line: {line}", file=sys.stderr)

    return timestamps


def download_youtube_audio(url: str, output_dir: str = "downloads", force_download: bool = False) -> str:
    """
    Download YouTube video as MP3.
    If the file already exists in the output directory, skip downloading unless force_download is True.

    Args:
        url: YouTube URL
        output_dir: Directory to save the downloaded file
        force_download: If True, re-download even if file exists

    Returns:
        Path to downloaded MP3 file
    """
    os.makedirs(output_dir, exist_ok=True)

    output_template = os.path.join(output_dir, '%(title)s.%(ext)s')

    # First, get video info without downloading to check if file exists
    info_opts = {
        'quiet': True,
        'no_warnings': True,
    }

    print(f"Checking video info: {url}")

    with yt_dlp.YoutubeDL(info_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        # Construct what the filename would be
        temp_opts = {'outtmpl': output_template}
        with yt_dlp.YoutubeDL(temp_opts) as temp_ydl:
            filename = temp_ydl.prepare_filename(info)
            mp3_filename = os.path.splitext(filename)[0] + '.mp3'

    # Check if file already exists and we're not forcing download
    if os.path.exists(mp3_filename) and not force_download:
        file_size_mb = os.path.getsize(mp3_filename) / (1024 * 1024)
        print(f"✓ File already exists ({file_size_mb:.1f} MB): {mp3_filename}")
        print(f"  Skipping download. Use --force-download to re-download.")
        return mp3_filename

    if os.path.exists(mp3_filename) and force_download:
        print(f"Force re-download enabled. Removing existing file...")
        os.remove(mp3_filename)

    # File doesn't exist, proceed with download
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_template,
        'quiet': False,
        'no_warnings': False,
    }

    print(f"Downloading audio from: {url}")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        # Replace the extension with .mp3
        mp3_filename = os.path.splitext(filename)[0] + '.mp3'

    print(f"Downloaded: {mp3_filename}")
    return mp3_filename


def get_audio_duration(audio_file: str) -> float:
    """
    Get the duration of an audio file using ffprobe (more efficient than loading the whole file).

    Args:
        audio_file: Path to the audio file

    Returns:
        Duration in seconds
    """
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', audio_file],
            capture_output=True,
            text=True,
            check=True
        )
        return float(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to get audio duration: {e.stderr}")
    except ValueError:
        raise RuntimeError("Failed to parse audio duration from ffprobe output")


def split_audio_ffmpeg(audio_file: str, timestamps: List[Tuple[int, int, str]], output_dir: str = "output"):
    """
    Split audio file based on timestamps using ffmpeg directly.
    This is much more memory-efficient for large files than loading them into pydub.

    Args:
        audio_file: Path to the MP3 file
        timestamps: List of (start_ms, end_ms, track_name) tuples
        output_dir: Directory to save split files
    """
    # Verify file exists
    if not os.path.exists(audio_file):
        raise FileNotFoundError(f"Audio file not found: {audio_file}")

    file_size_mb = os.path.getsize(audio_file) / (1024 * 1024)
    file_size_gb = file_size_mb / 1024

    print(f"\nPreparing to split audio file: {audio_file}", flush=True)
    if file_size_gb >= 1.0:
        print(f"File size: {file_size_gb:.2f} GB", flush=True)
    else:
        print(f"File size: {file_size_mb:.1f} MB", flush=True)

    os.makedirs(output_dir, exist_ok=True)

    # Get duration using ffprobe (doesn't load the whole file)
    print("Getting audio duration...", flush=True)
    try:
        total_duration_sec = get_audio_duration(audio_file)
        total_duration_ms = int(total_duration_sec * 1000)
    except Exception as e:
        print(f"\n❌ Error getting audio duration: {e}", file=sys.stderr, flush=True)
        raise

    hours = int(total_duration_sec // 3600)
    minutes = int((total_duration_sec % 3600) // 60)
    seconds = int(total_duration_sec % 60)

    print(f"Total duration: {hours:02d}:{minutes:02d}:{seconds:02d} ({total_duration_sec:.1f} seconds)", flush=True)
    print(f"\nSplitting into {len(timestamps)} tracks using ffmpeg (memory-efficient mode)...\n", flush=True)

    # Track timing for ETA
    start_time = time.time()
    total_output_size = 0

    # Create progress bar with fixed description
    with tqdm(total=len(timestamps),
              desc="Overall Progress",
              unit="track",
              bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]',
              position=0,
              leave=True) as pbar:

        for i, (start_ms, end_ms, track_name) in enumerate(timestamps, 1):
            # If end_ms is None, use the total duration
            if end_ms is None:
                end_ms = total_duration_ms

            # Validate timestamps
            if start_ms > total_duration_ms:
                tqdm.write(f"⚠️  Warning: Track {i} start time ({start_ms/1000:.1f}s) is beyond audio duration ({total_duration_ms/1000:.1f}s). Skipping.")
                continue

            if end_ms > total_duration_ms:
                tqdm.write(f"⚠️  Warning: Track {i} end time ({end_ms/1000:.1f}s) is beyond audio duration. Using end of file.")
                end_ms = total_duration_ms

            # Sanitize filename
            safe_filename = re.sub(r'[<>:"/\\|?*]', '_', track_name)
            safe_filename = f"{i:03d} - {safe_filename}.mp3"
            output_path = os.path.join(output_dir, safe_filename)

            # Convert milliseconds to seconds for ffmpeg
            start_sec = start_ms / 1000.0
            duration_sec = (end_ms - start_ms) / 1000.0

            # Show what we're processing now (above the progress bar)
            tqdm.write(f"\n⏳ [{i:03d}/{len(timestamps)}] Processing: {track_name}")

            try:
                # Use ffmpeg to extract the segment with progress
                cmd = [
                    'ffmpeg',
                    '-y',  # Overwrite output file if exists
                    '-ss', str(start_sec),  # Start time
                    '-t', str(duration_sec),  # Duration
                    '-i', audio_file,  # Input file
                    '-c:a', 'libmp3lame',  # MP3 codec
                    '-b:a', '192k',  # Bitrate
                    '-loglevel', 'error',  # Only show errors
                    '-progress', 'pipe:1',  # Show progress to stdout
                    output_path
                ]

                # Run ffmpeg and capture output
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)

                # Get output file size
                output_size_mb = os.path.getsize(output_path) / (1024 * 1024)
                total_output_size += output_size_mb

                # Calculate statistics
                elapsed = time.time() - start_time
                avg_time_per_track = elapsed / i
                remaining_tracks = len(timestamps) - i
                eta_seconds = avg_time_per_track * remaining_tracks

                # Format ETA
                eta_min = int(eta_seconds // 60)
                eta_sec = int(eta_seconds % 60)

                # Write track completion info
                tqdm.write(f"   ✓ Saved: {safe_filename} ({output_size_mb:.1f} MB) | ETA: {eta_min:02d}:{eta_sec:02d}")

            except subprocess.CalledProcessError as e:
                tqdm.write(f"   ❌ Error extracting track {i}: {e.stderr}")
                raise
            except Exception as e:
                tqdm.write(f"   ❌ Error processing track {i}: {e}")
                raise

            # Update progress bar
            pbar.update(1)

    # Final statistics
    total_time = time.time() - start_time
    total_min = int(total_time // 60)
    total_sec = int(total_time % 60)
    avg_time = total_time / len(timestamps)

    print(f"\n{'='*60}", flush=True)
    print(f"✓ Successfully split {len(timestamps)} tracks!", flush=True)
    print(f"  Total output size: {total_output_size:.1f} MB ({total_output_size/1024:.2f} GB)", flush=True)
    print(f"  Total time: {total_min:02d}:{total_sec:02d}", flush=True)
    print(f"  Average time per track: {avg_time:.1f}s", flush=True)
    print(f"  Output directory: {output_dir}", flush=True)
    print(f"{'='*60}\n", flush=True)


def split_audio(audio_file: str, timestamps: List[Tuple[int, int, str]], output_dir: str = "output"):
    """
    Split audio file based on timestamps.
    For large files (>500MB), uses ffmpeg directly for memory efficiency.
    For smaller files, uses pydub for convenience.

    Args:
        audio_file: Path to the MP3 file
        timestamps: List of (start_ms, end_ms, track_name) tuples
        output_dir: Directory to save split files
    """
    # Check file size
    file_size_mb = os.path.getsize(audio_file) / (1024 * 1024)

    # For files larger than 500MB, use ffmpeg directly to avoid loading into memory
    if file_size_mb > 500:
        print(f"Large file detected ({file_size_mb:.1f} MB). Using memory-efficient ffmpeg mode.")
        return split_audio_ffmpeg(audio_file, timestamps, output_dir)

    # For smaller files, use the original pydub method
    print(f"Using pydub for processing.")

    # Verify file exists
    if not os.path.exists(audio_file):
        raise FileNotFoundError(f"Audio file not found: {audio_file}")

    print(f"\nLoading audio file: {audio_file}")
    print(f"File size: {file_size_mb:.1f} MB")

    os.makedirs(output_dir, exist_ok=True)

    try:
        audio = AudioSegment.from_mp3(audio_file)
    except Exception as e:
        print(f"\n❌ Error loading MP3 file. This usually means ffmpeg is not installed or not accessible.", file=sys.stderr)
        print(f"Technical error: {e}", file=sys.stderr)
        raise

    total_duration = len(audio)

    print(f"Total duration: {total_duration / 1000:.2f} seconds ({total_duration / 60000:.1f} minutes)")
    print(f"\nSplitting into {len(timestamps)} tracks...\n")

    for i, (start_ms, end_ms, track_name) in enumerate(timestamps, 1):
        # If end_ms is None, use the total duration
        if end_ms is None:
            end_ms = total_duration

        # Validate timestamps
        if start_ms > total_duration:
            print(f"Warning: Track {i} start time ({start_ms/1000:.1f}s) is beyond audio duration ({total_duration/1000:.1f}s). Skipping.", file=sys.stderr)
            continue

        if end_ms > total_duration:
            print(f"Warning: Track {i} end time ({end_ms/1000:.1f}s) is beyond audio duration. Using end of file.", file=sys.stderr)
            end_ms = total_duration

        # Sanitize filename
        safe_filename = re.sub(r'[<>:"/\\|?*]', '_', track_name)
        safe_filename = f"{i:03d} - {safe_filename}.mp3"
        output_path = os.path.join(output_dir, safe_filename)

        print(f"Extracting: {safe_filename}")
        print(f"  Time: {start_ms/1000:.2f}s - {end_ms/1000:.2f}s")

        try:
            # Extract segment
            segment = audio[start_ms:end_ms]

            # Export
            segment.export(output_path, format="mp3", bitrate="192k")
            print(f"  Saved: {output_path}\n")
        except Exception as e:
            print(f"  Error exporting track {i}: {e}", file=sys.stderr)
            raise

    print(f"All tracks saved to: {output_dir}")


def sanitize_filename(name: str) -> str:
    """Remove or replace invalid filename characters."""
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def main():
    parser = argparse.ArgumentParser(
        description='Download YouTube video as MP3 and split it based on timestamps',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python youtube_mp3_splitter.py "https://www.youtube.com/watch?v=..." timestamps.txt
  python youtube_mp3_splitter.py -o my_tracks "https://youtube.com/..." timestamps.txt

Timestamps file format (one per line):
  00:00 - 03:45 First Track
  03:45 - 07:30 Second Track

Or simply:
  00:00 First Track
  03:45 Second Track
  07:30 Third Track
        """
    )

    parser.add_argument('url', help='YouTube URL')
    parser.add_argument('timestamps', help='Path to timestamps file')
    parser.add_argument('-o', '--output', default='output',
                        help='Output directory for split files (default: output)')
    parser.add_argument('-d', '--download-dir', default='downloads',
                        help='Directory for downloaded MP3 (default: downloads)')
    parser.add_argument('--keep-original', action='store_true',
                        help='Keep the original downloaded MP3 file')
    parser.add_argument('--force-download', action='store_true',
                        help='Force re-download even if file already exists')

    args = parser.parse_args()

    # Check if ffmpeg is available
    if not check_ffmpeg():
        sys.exit(1)

    # Check if timestamps file exists
    if not os.path.isfile(args.timestamps):
        print(f"Error: Timestamps file not found: {args.timestamps}", file=sys.stderr)
        sys.exit(1)

    # Parse timestamps
    print("Parsing timestamps file...")
    timestamps = parse_timestamps_file(args.timestamps)

    if not timestamps:
        print("Error: No valid timestamps found in file", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(timestamps)} tracks\n")

    # Download audio
    try:
        audio_file = download_youtube_audio(args.url, args.download_dir, args.force_download)
    except Exception as e:
        print(f"\n❌ Error downloading audio: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Verify the downloaded file exists
    if not os.path.exists(audio_file):
        print(f"\n❌ Error: Downloaded file not found at: {audio_file}", file=sys.stderr)
        print(f"Download directory contents:", file=sys.stderr)
        try:
            for item in os.listdir(args.download_dir):
                print(f"  - {item}", file=sys.stderr)
        except:
            pass
        sys.exit(1)

    # Split audio
    try:
        split_audio(audio_file, timestamps, args.output)
    except FileNotFoundError as e:
        print(f"\n❌ {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error splitting audio: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Clean up original file if requested
    if not args.keep_original:
        print(f"\nRemoving original file: {audio_file}")
        os.remove(audio_file)

    print("\nDone!")


if __name__ == '__main__':
    main()
