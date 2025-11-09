.PHONY: help build run split clean rebuild shell test

# Default target
.DEFAULT_GOAL := help

# Docker image name
IMAGE_NAME := youtube-mp3-splitter:latest

help: ## Show this help message
	@echo "YouTube MP3 Splitter - Makefile Commands"
	@echo "=========================================="
	@echo ""
	@echo "Usage: make [command]"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Examples:"
	@echo "  make split URL=\"https://youtube.com/...\" TIMESTAMPS=timestamps.txt"
	@echo "  make split URL=\"https://youtube.com/...\" TIMESTAMPS=timestamps.txt OUTPUT=my_chapters"
	@echo "  make split URL=\"https://youtube.com/...\" TIMESTAMPS=timestamps.txt FORCE=1"

build: ## Build the Docker image
	@echo "Building Docker image..."
	@docker build -t $(IMAGE_NAME) .
	@echo "✓ Build complete!"

rebuild: ## Rebuild the Docker image (no cache)
	@echo "Rebuilding Docker image from scratch..."
	@docker build --no-cache -t $(IMAGE_NAME) .
	@echo "✓ Rebuild complete!"

run: ## Run the container (alias for split)
	@$(MAKE) split

split: ## Split YouTube video (requires URL and TIMESTAMPS vars)
	@mkdir -p downloads output
ifndef URL
	@echo "❌ Error: URL is required"
	@echo "Usage: make split URL=\"https://youtube.com/...\" TIMESTAMPS=timestamps.txt"
	@exit 1
endif
ifndef TIMESTAMPS
	@echo "❌ Error: TIMESTAMPS file is required"
	@echo "Usage: make split URL=\"https://youtube.com/...\" TIMESTAMPS=timestamps.txt"
	@exit 1
endif
	@echo "Starting YouTube MP3 Splitter..."
	@docker run --rm \
		-v "$$(pwd):/data" \
		-w /data \
		$(IMAGE_NAME) \
		$(if $(OUTPUT),-o $(OUTPUT),) \
		$(if $(DOWNLOAD_DIR),-d $(DOWNLOAD_DIR),) \
		$(if $(KEEP),--keep-original,) \
		$(if $(FORCE),--force-download,) \
		"$(URL)" "$(TIMESTAMPS)"

shell: ## Open a shell in the container for debugging
	@docker run --rm -it \
		-v "$$(pwd):/data" \
		-w /data \
		--entrypoint /bin/bash \
		$(IMAGE_NAME)

test: ## Test the script with example timestamps
	@echo "Running test with example timestamps..."
	@if [ ! -f timestamps_example.txt ]; then \
		echo "❌ Error: timestamps_example.txt not found"; \
		exit 1; \
	fi
	@docker run --rm \
		-v "$$(pwd):/data" \
		-w /data \
		$(IMAGE_NAME) --help

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
s: split ## Shortcut for 'split'
b: build ## Shortcut for 'build'
c: clean ## Shortcut for 'clean'
h: help ## Shortcut for 'help'
