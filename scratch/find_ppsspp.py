#!/usr/bin/env ./.venv/bin/python3
import paramiko
import os

DEVICE_IP = "10.0.2.1"
USER = "spruce"
PASSWORD = "happygaming"

def search_device():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {DEVICE_IP}...")
    try:
        client.connect(DEVICE_IP, 22, USER, PASSWORD)
        print("Searching for ppsspp*.ini files on device...")
        stdin, stdout, stderr = client.exec_command('find /mnt/sdcard -name "ppsspp*.ini" 2>/dev/null')
        paths = stdout.read().decode().splitlines()
        
        if not paths:
            print("No PPSSPP ini files found.")
        else:
            print("\nFound the following configuration files:")
            for p in paths:
                print(f" -> {p}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    search_device()
