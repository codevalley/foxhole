# Use the official Python 3.12 image from Docker Hub
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    sudo \
    redis-server \
    wget \
    openssh-server \
    && rm -rf /var/lib/apt/lists/*

# Configure Redis to listen on all interfaces
RUN sed -i 's/bind 127.0.0.1 -::1/bind 0.0.0.0/' /etc/redis/redis.conf

# Set the working directory
WORKDIR /workspace

# Install Redis CLI
RUN apt-get update && apt-get install -y redis-tools && rm -rf /var/lib/apt/lists/*

# Install MinIO client
RUN curl https://dl.min.io/client/mc/release/linux-amd64/mc -o /usr/local/bin/mc \
    && chmod +x /usr/local/bin/mc

# Install MinIO server
RUN wget https://dl.min.io/server/minio/release/linux-amd64/minio \
    && chmod +x minio \
    && mv minio /usr/local/bin/

# Create vscode user
RUN useradd -m -s /bin/bash -u 1000 vscode \
    && usermod -aG sudo vscode \
    && echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Create and set permissions for MinIO data directory
RUN mkdir -p /data && chown vscode:vscode /data

# Set ownership of the workspace directory
RUN chown -R vscode:vscode /workspace

# SSH Configuration
RUN mkdir /var/run/sshd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

# Copy startup script
COPY startup.sh /usr/local/bin/startup.sh
RUN chmod +x /usr/local/bin/startup.sh

# Expose FastAPI port, Redis port, MinIO ports, and SSH port
EXPOSE 8000 6379 9000 9001 22

# Set the default command to our startup script
CMD ["/usr/local/bin/startup.sh"]

# Add volume for MinIO data
VOLUME ["/data"]
