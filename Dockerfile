FROM python:3.11-slim

# Install ffmpeg and other dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY youtube_mp3_splitter.py .

# Create directories for downloads and output
RUN mkdir -p /app/downloads /app/output

# Set volumes for data persistence
VOLUME ["/app/downloads", "/app/output"]

# Set the entrypoint to the script
ENTRYPOINT ["python", "youtube_mp3_splitter.py"]

# Default help command
CMD ["--help"]
