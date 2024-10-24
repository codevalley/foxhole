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

# Create a .env file with necessary environment variables
cat << EOF > .env
DATABASE_URL=sqlite:///./data/app.db
REDIS_URL=redis://redis:6379
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=foxhole
EOF

# Build and start the Docker containers
sudo docker-compose up -d --build

echo "Deployment completed!"
