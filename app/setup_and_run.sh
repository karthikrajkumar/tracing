#!/bin/bash

# Setup and run script for the OpenTelemetry tracing demo

# Set up colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up OpenTelemetry tracing demo...${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3 and try again.${NC}"
    exit 1
fi

# Create a virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate the virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt

# Create data directory if it doesn't exist
mkdir -p data

# Check if Jaeger is running
echo -e "${YELLOW}Checking if Jaeger is running...${NC}"
if ! curl -s http://localhost:16686 > /dev/null; then
    echo -e "${RED}Jaeger doesn't seem to be running. Please start Jaeger first.${NC}"
    echo -e "You can start Jaeger with: cd ../jaeger/jaeger-1.52.0-darwin-amd64 && ./jaeger-all-in-one"
    exit 1
fi

# Check if Prometheus is running
echo -e "${YELLOW}Checking if Prometheus is running...${NC}"
if ! curl -s http://localhost:9090 > /dev/null; then
    echo -e "${RED}Prometheus doesn't seem to be running. Please start Prometheus first.${NC}"
    echo -e "You can start Prometheus with: cd ../prometheus && prometheus --config.file=prometheus.yml"
    exit 1
fi

# Start the FastAPI application
echo -e "${GREEN}Starting FastAPI application...${NC}"
uvicorn main:app --reload

# Note: This script will keep running until you press Ctrl+C to stop the FastAPI application
