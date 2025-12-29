.PHONY: help build run split download dl clean rebuild shell test

# Default target
.DEFAULT_GOAL := help

# Docker image name
IMAGE_NAME := youtube-mp3-splitter:latest

help: ## Show this help message
	@echo "YouTube MP3 Splitter - Makefile Commands"
	@echo "=========================================="
	@echo ""
	@echo "Usage: make [command] [arguments]"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Examples:"
	@echo "  make run https://youtube.com/watch?v=... timestamps.txt"
	@echo "  make run https://youtube.com/... timestamps.txt --force-download"
	@echo "  make download https://youtube.com/watch?v=...  # MP3 only, no splitting"

build: ## Build the Docker image
	@echo "Building Docker image..."
	@docker build -t $(IMAGE_NAME) .
	@echo "✓ Build complete!"

rebuild: ## Rebuild the Docker image (no cache)
	@echo "Rebuilding Docker image from scratch..."
	@docker build --no-cache -t $(IMAGE_NAME) .
	@echo "✓ Rebuild complete!"

run: ## Run the splitter: make run URL TIMESTAMPS [OPTIONS]
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "❌ Error: URL and TIMESTAMPS are required"; \
		echo "Usage: make run <youtube-url> <timestamps-file> [options]"; \
		echo "Example: make run https://youtube.com/... timestamps.txt --force-download"; \
		exit 1; \
	fi
	@mkdir -p downloads output
	@echo "Starting YouTube MP3 Splitter..."
	@docker run --rm \
		-v "$$(pwd):/data" \
		-w /data \
		$(IMAGE_NAME) $(filter-out $@,$(MAKECMDGOALS))

split: run ## Alias for 'run'

download: ## Download MP3 only (no splitting): make download URL
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "❌ Error: URL is required"; \
		echo "Usage: make download <youtube-url>"; \
		echo "Example: make download https://youtube.com/watch?v=..."; \
		exit 1; \
	fi
	@mkdir -p downloads
	@echo "Downloading MP3 (no splitting)..."
	@docker run --rm \
		-v "$$(pwd)/downloads:/downloads" \
		-w /downloads \
		--entrypoint yt-dlp \
		$(IMAGE_NAME) -x --audio-format mp3 -o "%(title)s.%(ext)s" $(filter-out $@,$(MAKECMDGOALS))
	@echo "✓ Download complete! File saved to downloads/"

dl: download ## Shortcut for 'download'

# This allows any arguments after the target to be treated as arguments, not targets
%:
	@:

shell: ## Open a shell in the container for debugging
	@docker run --rm -it \
		-v "$$(pwd):/data" \
		-w /data \
		--entrypoint /bin/bash \
		$(IMAGE_NAME)

clean: ## Clean up generated files and directories
	@echo "Cleaning up..."
	@rm -rf output/* downloads/*
	@echo "✓ Cleaned output and downloads directories"

clean-all: clean ## Clean everything including Docker image
	@echo "Removing Docker image..."
	@docker rmi $(IMAGE_NAME) 2>/dev/null || true
	@echo "✓ Removed Docker image"

version: ## Show version info
	@echo "YouTube MP3 Splitter"
	@echo "Docker Image: $(IMAGE_NAME)"
	@docker run --rm $(IMAGE_NAME) --help | head -n 3

logs: ## Show recent container logs (if any running)
	@docker ps -a --filter ancestor=$(IMAGE_NAME) --format "{{.ID}}" | xargs -r docker logs

# Quick shortcuts
s: run ## Shortcut for 'run'
r: run ## Shortcut for 'run'
b: build ## Shortcut for 'build'
c: clean ## Shortcut for 'clean'
h: help ## Shortcut for 'help'
