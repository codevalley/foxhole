#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get the app container name/ID
APP_CONTAINER=$(docker-compose ps -q app)

if [ -z "$APP_CONTAINER" ]; then
    echo -e "${RED}Error: App container not found. Is the application running?${NC}"
    exit 1
fi

# Copy the inspection script into the container
echo -e "${GREEN}Copying inspection script to container...${NC}"
docker cp foxhole_inspector.py $APP_CONTAINER:/utils/foxhole_inspector.py

# Install required packages in the container
echo -e "${GREEN}Installing required packages...${NC}"
docker exec $APP_CONTAINER pip install minio redis

# Function to run the inspector with arguments
function run_inspector() {
    echo -e "${GREEN}Running inspection...${NC}"
    docker exec $APP_CONTAINER python /utils/foxhole_inspector.py "$@"
}

# Show help if no arguments
if [ $# -eq 0 ]; then
    run_inspector --help
    exit 0
fi

# Run with provided arguments
run_inspector "$@"

# Cleanup
echo -e "${GREEN}Cleaning up...${NC}"
docker exec $APP_CONTAINER rm /utils/foxhole_inspector.py

echo -e "${GREEN}Done!${NC}"
