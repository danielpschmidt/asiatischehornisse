#!/bin/bash

# Set GEOS environment variables
export GEOS_INCLUDE_PATH=$(brew --prefix geos)/include
export GEOS_LIBRARY_PATH=$(brew --prefix geos)/lib

# Install Python packages
pip install --no-cache-dir -r requirements.txt

echo "Setup complete! You can now run the application with: python app.py"
