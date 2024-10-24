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
git clone https://github.com/yourusername/foxhole.git
cd foxhole

# Copy the production environment file
cp .env.production .env

# Create necessary directories
mkdir -p data certbot/conf certbot/www

# Stop and remove existing containers
sudo docker-compose down

# Remove old images
sudo docker-compose rm -f

# Pull latest changes
git pull origin main

# Start Nginx and Certbot containers
sudo docker-compose up -d nginx certbot

# Replace 'yourdomain.com' with your actual domain
DOMAIN="your-actual-domain.com"

# Generate SSL certificate
sudo docker-compose run --rm certbot certonly --webroot --webroot-path /var/www/certbot -d $DOMAIN

# Restart Nginx to apply SSL changes
sudo docker-compose restart nginx

# Build and start the remaining Docker containers
sudo docker-compose up -d --build

echo "Deployment completed!"
