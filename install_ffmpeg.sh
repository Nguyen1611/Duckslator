#!/bin/bash

# Update package lists
echo "Updating package lists..."
sudo apt-get update

# Install ffmpeg
echo "Installing ffmpeg..."
sudo apt-get install -y ffmpeg

# Verify installation
echo "Verifying ffmpeg installation..."
ffmpeg -version

# Confirmation message
echo "ffmpeg has been installed successfully."
