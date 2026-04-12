#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: $0 <device_ip> [username]"
    echo "Example: $0 192.168.1.100 root"
    exit 1
fi

DEVICE_IP=$1
USER=${2:-root}  # Default to root if no username is provided
REMOTE_APP_DIR="/mnt/SDCARD/App"
FOLDER_NAME="RA_Manager"

echo "========================================="
echo " Pushing RA_Manager to $DEVICE_IP"
echo "========================================="

# 1. Delete the old revision cleanly
echo "1) Deleting old revision on device..."
ssh "$USER@$DEVICE_IP" "rm -rf \"$REMOTE_APP_DIR/$FOLDER_NAME\""
if [ $? -ne 0 ]; then
    echo "[!] Could not connect or remove old directory. Check SSH connection."
    exit 1
fi

# 2. Re-create the deploy payload internally just to be safe
echo "2) Re-building deployment..."
bash update_deploy.sh > /dev/null

# 3. Secure Copy the new contents over
echo "3) Uploading new deployment to device via SCP..."
scp -r "deploy/$FOLDER_NAME" "$USER@$DEVICE_IP:$REMOTE_APP_DIR/"
if [ $? -eq 0 ]; then
    echo "========================================="
    echo " ✅ Push Complete! The app is updated."
    echo "========================================="
else
    echo "[!] Upload failed!"
    exit 1
fi
