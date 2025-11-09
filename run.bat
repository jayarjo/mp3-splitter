@echo off
REM Wrapper script to run YouTube MP3 Splitter in Docker (Windows)

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not installed.
    echo Please install Docker from https://docs.docker.com/get-docker/
    exit /b 1
)

REM Check if image exists, if not build it
docker images -q youtube-mp3-splitter:latest >nul 2>&1
if errorlevel 1 (
    echo Building Docker image...
    docker build -t youtube-mp3-splitter:latest .
    echo Image built successfully!
)

REM Create output directories if they don't exist
if not exist "downloads" mkdir downloads
if not exist "output" mkdir output

REM Run the container
echo Running YouTube MP3 Splitter...
docker run --rm ^
    -v "%cd%:/data" ^
    -w /data ^
    youtube-mp3-splitter:latest %*
