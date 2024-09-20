# Foxhole Backend Deployment Guide

This guide will walk you through the process of deploying the Foxhole Backend on a server (DigitalOcean droplet, EC2 instance, etc.).

## Prerequisites

- A server running Ubuntu 20.04 or later
- Docker installed on the server
- Git installed on the server
- Access to a Docker registry (e.g., Docker Hub)

## Step 1: Clone the Repository

1. SSH into your server
2. Clone the repository:

   ```bash
   git clone https://github.com/your-username/foxhole-backend.git
   cd foxhole-backend
   ```

## Step 2: Set Up Environment Variables

1. Create a `.env` file in the project root:

   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and fill in the necessary values:

   ```bash
   nano .env
   ```

## Step 3: Build and Push Docker Image

1. Log in to your Docker registry:

   ```bash
   docker login
   ```

2. Build the Docker image:

   ```bash
   docker build -t your-registry/foxhole-backend:latest .
   ```

3. Push the image to your registry:

   ```bash
   docker push your-registry/foxhole-backend:latest
   ```

## Step 4: Install Kamal

1. Install Kamal:

   ```bash
   gem install kamal
   ```

## Step 5: Configure Kamal

1. Create a `config/deploy.yml` file if it doesn't exist:

   ```bash
   mkdir -p config
   touch config/deploy.yml
   ```

2. Edit the `config/deploy.yml` file with your deployment configuration:

   ```bash
   nano config/deploy.yml
   ```

   (Refer to the existing `config/deploy.yml` file in the repository for the structure)

## Step 6: Set Up Secrets

1. Create a `.env.production` file with your production environment variables:

   ```bash
   cp .env.example .env.production
   nano .env.production
   ```

2. Fill in the production values in `.env.production`

## Step 7: Deploy with Kamal

1. Deploy the application:

   ```bash
   kamal setup
   kamal deploy
   ```

## Step 8: Verify Deployment

1. Check if the application is running:

   ```bash
   kamal app status
   ```

2. Access the application's health check endpoint:

   ```bash
   curl http://your-server-ip:8000/health
   ```

## Troubleshooting

- If you encounter any issues, check the logs:

  ```bash
  kamal app logs
  ```

- To restart the application:

  ```bash
  kamal app restart
  ```

## Updating the Application

To update the application with new changes:

1. Pull the latest changes from the repository
2. Rebuild and push the Docker image
3. Run `kamal deploy`

## Additional Resources

- [Kamal Documentation](https://kamal-deploy.org/)
- [Docker Documentation](https://docs.docker.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

For any further assistance, please refer to the project's README or open an issue on the GitHub repository.
