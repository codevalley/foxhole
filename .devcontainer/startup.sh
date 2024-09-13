#!/bin/bash

# Start Redis
sudo service redis-server start

# Start MinIO
nohup minio server /data --console-address :9001 > /tmp/minio.log 2>&1 &

# Wait for MinIO to start
sleep 5

# Set up MinIO alias
mc alias set myminio http://localhost:9000 minioadmin minioadmin

# Keep the script running
tail -f /dev/null
