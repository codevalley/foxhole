#!/bin/bash

echo "Starting Redis..."
sudo service redis-server start
sleep 2
if redis-cli ping > /dev/null 2>&1; then
    echo "Redis started successfully"
else
    echo "Failed to start Redis"
fi

echo "Starting MinIO..."
nohup minio server /data --console-address :9001 > /tmp/minio.log 2>&1 &

echo "Waiting for MinIO to initialize..."
for i in {1..30}; do
    if curl -s http://localhost:9000/minio/health/live; then
        echo "MinIO started successfully"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Failed to start MinIO"
    fi
    sleep 1
done

echo "Attempting to set MinIO alias..."
if mc alias set myminio http://localhost:9000 minioadmin minioadmin; then
    echo "MinIO alias set successfully"
else
    echo "Failed to set MinIO alias"
fi

echo "Checking MinIO status..."
if mc admin info myminio; then
    echo "MinIO is operational"
else
    echo "Failed to get MinIO info"
fi

echo "Starting SSH server..."
sudo service ssh start
if [ $? -eq 0 ]; then
    echo "SSH server started successfully"
else
    echo "Failed to start SSH server"
fi

# Keep the script running
tail -f /dev/null
