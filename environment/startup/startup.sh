#!/bin/bash

# Startup script for additional container configuration
# This script runs automatically when the container starts if it exists
# Place any pre-loading, downloads, or additional setup operations here

# Note: We don't use 'set -e' here because we want to continue even if some downloads fail

# Colors for output
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
CYAN="\033[1;36m"
NC="\033[0m" # No Color

echo -e "${CYAN}>> Running startup script...${NC}"

# Pre-load lungmask models to avoid downloading during job execution
# This ensures models are available even if the container loses internet access during runtime

LUNGMASK_CACHE_DIR="/root/.cache/torch/hub/checkpoints"
MODELS_TO_DOWNLOAD=(
    "https://github.com/JoHof/lungmask/releases/download/v0.0/unet_r231-d5d2fc3d.pth"
    "https://github.com/JoHof/lungmask/releases/download/v0.0/unet_ltrclobes-d5d2fc3d.pth"
    "https://github.com/JoHof/lungmask/releases/download/v0.0/unet_r231covidweb-d5d2fc3d.pth"
)

# Create cache directory if it doesn't exist
mkdir -p "$LUNGMASK_CACHE_DIR"

# Download each model if it doesn't already exist
for model_url in "${MODELS_TO_DOWNLOAD[@]}"; do
    model_filename=$(basename "$model_url")
    model_path="$LUNGMASK_CACHE_DIR/$model_filename"
    
    if [ -f "$model_path" ]; then
        echo -e "${GREEN}>> Model $model_filename already exists, skipping download${NC}"
    else
        echo -e "${CYAN}>> Downloading model: $model_filename${NC}"
        if curl -L -f -o "$model_path" "$model_url" 2>/dev/null; then
            echo -e "${GREEN}>> Successfully downloaded $model_filename${NC}"
        else
            echo -e "${YELLOW}>> Warning: Failed to download $model_filename (may retry during job execution)${NC}"
            # Don't fail the startup if download fails - job can retry
        fi
    fi
done

echo -e "${GREEN}>> Startup script completed${NC}"

