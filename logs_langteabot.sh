#!/bin/bash

# Step 1: Get the container ID by its name and store ID to the system variable
CONTAINER_NAME="telegram_bot_docker_langteabot_1"
CONTAINER_ID=$(docker ps -aqf "name=$CONTAINER_NAME")

# Step 2: Get logs by this ID
docker logs $CONTAINER_ID