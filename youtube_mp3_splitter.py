#!/usr/bin/env python3
"""
YouTube MP3 Splitter
Downloads a YouTube video as MP3 and splits it into separate files based on timestamps.
"""

import argparse
import os
import sys
import re
from pathlib import Path
from typing import List, Tuple
import yt_dlp
from pydub import AudioSegment


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


def download_youtube_audio(url: str, output_dir: str = "downloads") -> str:
    """
    Download YouTube video as MP3.

    Args:
        url: YouTube URL
        output_dir: Directory to save the downloaded file

    Returns:
        Path to downloaded MP3 file
    """
    os.makedirs(output_dir, exist_ok=True)

    output_template = os.path.join(output_dir, '%(title)s.%(ext)s')

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


def split_audio(audio_file: str, timestamps: List[Tuple[int, int, str]], output_dir: str = "output"):
    """
    Split audio file based on timestamps.

    Args:
        audio_file: Path to the MP3 file
        timestamps: List of (start_ms, end_ms, track_name) tuples
        output_dir: Directory to save split files
    """
    os.makedirs(output_dir, exist_ok=True)

    print(f"\nLoading audio file: {audio_file}")
    audio = AudioSegment.from_mp3(audio_file)
    total_duration = len(audio)

    print(f"Total duration: {total_duration / 1000:.2f} seconds")
    print(f"\nSplitting into {len(timestamps)} tracks...\n")

    for i, (start_ms, end_ms, track_name) in enumerate(timestamps, 1):
        # If end_ms is None, use the total duration
        if end_ms is None:
            end_ms = total_duration

        # Sanitize filename
        safe_filename = re.sub(r'[<>:"/\\|?*]', '_', track_name)
        safe_filename = f"{i:02d} - {safe_filename}.mp3"
        output_path = os.path.join(output_dir, safe_filename)

        print(f"Extracting: {safe_filename}")
        print(f"  Time: {start_ms/1000:.2f}s - {end_ms/1000:.2f}s")

        # Extract segment
        segment = audio[start_ms:end_ms]

        # Export
        segment.export(output_path, format="mp3", bitrate="192k")
        print(f"  Saved: {output_path}\n")

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

    args = parser.parse_args()

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
        audio_file = download_youtube_audio(args.url, args.download_dir)
    except Exception as e:
        print(f"Error downloading audio: {e}", file=sys.stderr)
        sys.exit(1)

    # Split audio
    try:
        split_audio(audio_file, timestamps, args.output)
    except Exception as e:
        print(f"Error splitting audio: {e}", file=sys.stderr)
        sys.exit(1)

    # Clean up original file if requested
    if not args.keep_original:
        print(f"\nRemoving original file: {audio_file}")
        os.remove(audio_file)

    print("\nDone!")


if __name__ == '__main__':
    main()
