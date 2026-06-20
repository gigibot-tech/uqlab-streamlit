#!/bin/bash

# Start MinIO with uvicorn backend
# This script starts MinIO via docker-compose, waits for it to be healthy,
# then starts the uvicorn backend server.

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting uqlab-streamlit with MinIO storage backend${NC}"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: docker-compose or docker is not installed${NC}"
    exit 1
fi

# Determine docker compose command
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

# Start MinIO
echo -e "${YELLOW}Starting MinIO...${NC}"
$DOCKER_COMPOSE up -d minio

# Wait for MinIO to be healthy
echo -e "${YELLOW}Waiting for MinIO to be healthy...${NC}"
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if $DOCKER_COMPOSE ps minio | grep -q "healthy"; then
        echo -e "${GREEN}MinIO is healthy!${NC}"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo -e "${RED}Error: MinIO failed to become healthy after ${MAX_RETRIES} attempts${NC}"
        echo -e "${YELLOW}Check logs with: $DOCKER_COMPOSE logs minio${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}Waiting... (attempt $RETRY_COUNT/$MAX_RETRIES)${NC}"
    sleep 2
done

# Initialize bucket (run minio-init service)
echo -e "${YELLOW}Initializing MinIO bucket...${NC}"
$DOCKER_COMPOSE up minio-init

# Display MinIO info
echo -e "${GREEN}MinIO is running!${NC}"
echo -e "  API endpoint:     http://localhost:9000"
echo -e "  Console:          http://localhost:9001"
echo -e "  Username:         minioadmin"
echo -e "  Password:         minioadmin"
echo -e "  Default bucket:   uqlab-artifacts"
echo ""

# Start uvicorn backend
echo -e "${YELLOW}Starting uvicorn backend...${NC}"
cd backend

# Trap SIGINT and SIGTERM to gracefully shutdown
trap 'echo -e "\n${YELLOW}Shutting down...${NC}"; kill $UVICORN_PID 2>/dev/null; exit 0' INT TERM

# Start uvicorn in background
uvicorn app.main:app --reload &
UVICORN_PID=$!

echo -e "${GREEN}Backend started with PID $UVICORN_PID${NC}"
echo -e "${GREEN}Storage backend: S3 (local MinIO at http://localhost:9000)${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop both MinIO and the backend${NC}"

# Wait for uvicorn process
wait $UVICORN_PID

# Made with Bob
