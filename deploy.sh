#!/bin/bash

# Update the system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone your repository (replace with your actual repository URL)
git clone https://github.com/yourusername/foxhole-backend.git
cd foxhole-backend

# Copy the production environment file
cp .env.production .env

# Build and start the Docker containers
sudo docker-compose up -d --build

echo "Deployment completed!"
