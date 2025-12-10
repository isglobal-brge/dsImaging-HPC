#!/bin/bash
# Pre-startup script
# This script runs AFTER all dependencies are installed but BEFORE the container is considered "up"
# Use this for operations that need dependencies (Python, R, etc.) but must complete before services start
# Examples:
#   - Pre-downloading models or large files
#   - Running database migrations
#   - Validating configuration
#   - Pre-compiling code
#
# If this script fails, the container startup will abort
#
# This script is OPTIONAL - if it doesn't exist or is empty, startup will continue normally

set -e  # Abort on any error

# Colors for output
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
CYAN="\033[1;36m"
RED="\033[1;31m"
NC="\033[0m" # No Color

echo -e "${CYAN}>> Running pre-startup script...${NC}"

# Pre-load lungmask models to avoid downloading during job execution
# This ensures models are available even if the container loses internet access during runtime

# Use persistent storage for model caching (survives container rebuilds)
# The /persistent volume is mounted from dshpc-imaging-persistent-storage
PERSISTENT_MODEL_DIR="/persistent/models/torch_hub/checkpoints"
TORCH_CACHE_DIR="/root/.cache/torch/hub/checkpoints"

MODELS_TO_DOWNLOAD=(
    "https://github.com/JoHof/lungmask/releases/download/v0.0/unet_r231-d5d2fc3d.pth"
    "https://github.com/JoHof/lungmask/releases/download/v0.0/unet_ltrclobes-3a07043d.pth"
    "https://github.com/JoHof/lungmask/releases/download/v0.0/unet_r231covid-0de78a7e.pth"
)

# Create persistent model directory if it doesn't exist
mkdir -p "$PERSISTENT_MODEL_DIR"

# Create parent directory for torch cache and symlink to persistent storage
mkdir -p "$(dirname "$TORCH_CACHE_DIR")"
if [ -L "$TORCH_CACHE_DIR" ]; then
    # Symlink already exists, verify it points to the right place
    if [ "$(readlink "$TORCH_CACHE_DIR")" != "$PERSISTENT_MODEL_DIR" ]; then
        rm "$TORCH_CACHE_DIR"
        ln -s "$PERSISTENT_MODEL_DIR" "$TORCH_CACHE_DIR"
        echo -e "${CYAN}>> Updated symlink: $TORCH_CACHE_DIR -> $PERSISTENT_MODEL_DIR${NC}"
    fi
elif [ -d "$TORCH_CACHE_DIR" ]; then
    # Directory exists, move contents to persistent storage and replace with symlink
    echo -e "${CYAN}>> Migrating existing models to persistent storage...${NC}"
    mv "$TORCH_CACHE_DIR"/* "$PERSISTENT_MODEL_DIR"/ 2>/dev/null || true
    rm -rf "$TORCH_CACHE_DIR"
    ln -s "$PERSISTENT_MODEL_DIR" "$TORCH_CACHE_DIR"
    echo -e "${GREEN}>> Migrated models and created symlink${NC}"
else
    # No directory exists, create symlink
    ln -s "$PERSISTENT_MODEL_DIR" "$TORCH_CACHE_DIR"
    echo -e "${CYAN}>> Created symlink: $TORCH_CACHE_DIR -> $PERSISTENT_MODEL_DIR${NC}"
fi

# Download each model if it doesn't already exist
download_failed=false
for model_url in "${MODELS_TO_DOWNLOAD[@]}"; do
    model_filename=$(basename "$model_url")
    model_path="$PERSISTENT_MODEL_DIR/$model_filename"
    temp_path="${model_path}.tmp"

    if [ -f "$model_path" ]; then
        # Verify file is not corrupted (has some minimum size)
        file_size=$(stat -c%s "$model_path" 2>/dev/null || stat -f%z "$model_path" 2>/dev/null || echo "0")
        if [ "$file_size" -gt 1000000 ]; then
            echo -e "${GREEN}>> Model $model_filename already exists (${file_size} bytes), skipping download${NC}"
            continue
        else
            echo -e "${YELLOW}>> Model $model_filename appears corrupted (${file_size} bytes), re-downloading...${NC}"
            rm -f "$model_path"
        fi
    fi

    echo -e "${CYAN}>> Downloading model: $model_filename${NC}"
    # Download to temp file first to avoid partial downloads being used
    if curl -L -f --retry 3 --retry-delay 5 -o "$temp_path" "$model_url" 2>/dev/null; then
        # Verify downloaded file has reasonable size
        file_size=$(stat -c%s "$temp_path" 2>/dev/null || stat -f%z "$temp_path" 2>/dev/null || echo "0")
        if [ "$file_size" -gt 1000000 ]; then
            mv "$temp_path" "$model_path"
            echo -e "${GREEN}>> Successfully downloaded $model_filename (${file_size} bytes)${NC}"
        else
            echo -e "${RED}>> Error: Downloaded file $model_filename is too small (${file_size} bytes), likely corrupted${NC}"
            rm -f "$temp_path"
            download_failed=true
        fi
    else
        echo -e "${RED}>> Error: Failed to download $model_filename${NC}"
        rm -f "$temp_path"
        download_failed=true
    fi
done

# Check if any downloads failed
if [ "$download_failed" = true ]; then
    echo -e "${RED}>> One or more model downloads failed. Container startup aborted.${NC}"
    exit 1
fi

echo -e "${GREEN}>> Pre-startup script completed${NC}"
