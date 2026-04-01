#!/bin/bash

# Google Ads Assistant Setup Script

echo "===== Google Ads Assistant Setup ====="
echo "This script will help you set up the Google Ads Assistant application."

# Check if Python is installed
if command -v python3.12 &>/dev/null; then
    echo "Python is installed."
else
    echo "Error: Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3.12 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || { echo "Error: Failed to activate virtual environment."; exit 1; }

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt || { echo "Error: Failed to install dependencies."; exit 1; }

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.template .env
    echo ".env file created. Please edit it to add your API keys."
else
    echo ".env file already exists."
fi

echo "===== Setup Complete ====="
echo "To run the application:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run the application: streamlit run main.py"
echo "3. Open your browser at http://localhost:8501"

# Ask if user wants to run the application now
read -p "Do you want to run the application now? (y/n): " run_now
if [[ $run_now == "y" || $run_now == "Y" ]]; then
    echo "Starting the application..."
    streamlit run main.py
else
    echo "You can run the application later with: streamlit run main.py"
fi
