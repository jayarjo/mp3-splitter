#!/bin/bash
#
# Wrapper script to run YouTube MP3 Splitter in Docker
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed.${NC}"
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if image exists, if not build it
if [[ "$(docker images -q youtube-mp3-splitter:latest 2> /dev/null)" == "" ]]; then
    echo -e "${YELLOW}Building Docker image...${NC}"
    docker build -t youtube-mp3-splitter:latest .
    echo -e "${GREEN}Image built successfully!${NC}"
fi

# Create output directories if they don't exist
mkdir -p downloads output

# Run the container
echo -e "${GREEN}Running YouTube MP3 Splitter...${NC}"
docker run --rm \
    -v "$(pwd):/data" \
    -v "$(pwd)/output:/app/output" \
    -v "$(pwd)/downloads:/app/downloads" \
    -w /data \
    youtube-mp3-splitter:latest "$@"
