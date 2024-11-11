#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
INSPECTOR_SCRIPT="$SCRIPT_DIR/app/foxhole_inspector.py"

# Verify inspector script exists
if [ ! -f "$INSPECTOR_SCRIPT" ]; then
    echo -e "${RED}Error: Inspector script not found at $INSPECTOR_SCRIPT${NC}"
    exit 1
fi

# Get the app container name/ID
APP_CONTAINER=$(docker-compose ps -q app)

if [ -z "$APP_CONTAINER" ]; then
    echo -e "${RED}Error: App container not found. Is the application running?${NC}"
    exit 1
fi

# Copy the inspection script into the container
echo -e "${GREEN}Copying inspection script to container...${NC}"
docker cp "$INSPECTOR_SCRIPT" $APP_CONTAINER:/app/foxhole_inspector.py

# Install required packages in the container
echo -e "${GREEN}Installing required packages...${NC}"
docker exec $APP_CONTAINER pip install --quiet minio redis

# Function to run the inspector with arguments
function run_inspector() {
    echo -e "${GREEN}Running inspection...${NC}"
    docker exec $APP_CONTAINER python /app/foxhole_inspector.py "$@"
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
docker exec $APP_CONTAINER rm -f /app/foxhole_inspector.py

echo -e "${GREEN}Done!${NC}"
