#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up FastAPI Auto-Instrumentation Agent and Sample App${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3 and try again.${NC}"
    exit 1
fi

# Check if Docker is installed (for Jaeger)
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker is not installed. You'll need to run Jaeger manually.${NC}"
    DOCKER_AVAILABLE=false
else
    DOCKER_AVAILABLE=true
fi

# Create a virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install the auto-instrumentation agent
echo -e "${YELLOW}Installing FastAPI Auto-Instrumentation Agent...${NC}"
cd fastapi-auto-agent
pip install -e .
cd ..

# Install the sample app dependencies
echo -e "${YELLOW}Installing Sample FastAPI App dependencies...${NC}"
cd sample-fastapi-app
pip install -r requirements.txt
cd ..

# Start Jaeger if Docker is available
if [ "$DOCKER_AVAILABLE" = true ]; then
    echo -e "${YELLOW}Starting Jaeger...${NC}"
    docker run -d --name jaeger \
        -e COLLECTOR_OTLP_ENABLED=true \
        -p 16686:16686 \
        -p 4317:4317 \
        -p 4318:4318 \
        jaegertracing/all-in-one:latest
    
    # Wait for Jaeger to start
    echo -e "${YELLOW}Waiting for Jaeger to start...${NC}"
    sleep 5
else
    echo -e "${YELLOW}Please make sure Jaeger is running and accessible at http://localhost:16686${NC}"
    echo -e "${YELLOW}You can start Jaeger with Docker using:${NC}"
    echo -e "docker run -d --name jaeger -e COLLECTOR_OTLP_ENABLED=true -p 16686:16686 -p 4317:4317 -p 4318:4318 jaegertracing/all-in-one:latest"
    echo -e "${YELLOW}Press Enter to continue when Jaeger is running...${NC}"
    read
fi

# Run the sample app with auto-instrumentation
echo -e "${GREEN}Running Sample FastAPI App with Auto-Instrumentation...${NC}"
echo -e "${GREEN}The app will be available at http://localhost:8000${NC}"
echo -e "${GREEN}The Jaeger UI will be available at http://localhost:16686${NC}"
echo -e "${GREEN}Press Ctrl+C to stop the app${NC}"

cd sample-fastapi-app
fastapi-auto-agent --service-name sample-fastapi-app python -m uvicorn app.main:app --reload

# Cleanup
if [ "$DOCKER_AVAILABLE" = true ]; then
    echo -e "${YELLOW}Stopping Jaeger...${NC}"
    docker stop jaeger
    docker rm jaeger
fi

echo -e "${GREEN}Done!${NC}"
