#!/bin/bash

echo "Starting Redis..."
sudo service redis-server start
echo "Redis started"

echo "Starting MinIO..."
nohup minio server /data --console-address :9001 > /tmp/minio.log 2>&1 &
echo "MinIO start command executed"

echo "Waiting for MinIO to initialize..."
sleep 10

echo "Attempting to set MinIO alias..."
mc alias set myminio http://localhost:9000 minioadmin minioadmin
echo "MinIO alias set attempt completed"

echo "Checking MinIO status..."
mc admin info myminio

# Keep the script running
tail -f /dev/null
