#!/usr/bin/env ./.venv/bin/python3
import paramiko
from scp import SCPClient
import os
import sys

DEVICE_IP = "10.0.2.1"
USER = "spruce"
PASSWORD = "happygaming"
REMOTE_APP_DIR = "/mnt/SDCARD/App"
FOLDER_NAME = "RA_Manager"

def create_ssh_client(server, port, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password)
    return client

def run_local_build():
    print("1) Re-building deployment...")
    os.system("bash update_deploy.sh > /dev/null")

def deploy():
    run_local_build()
    
    print(f"2) Connecting to {DEVICE_IP} as {USER}...")
    try:
        ssh = create_ssh_client(DEVICE_IP, 22, USER, PASSWORD)
    except Exception as e:
        print(f"[!] Failed to connect: {e}")
        sys.exit(1)

    print("3) Grabbing runtime.log and settings.json from device...")
    try:
        with SCPClient(ssh.get_transport()) as scp:
            try:
                scp.get(f"{REMOTE_APP_DIR}/{FOLDER_NAME}/runtime.log", local_path="device_runtime.log")
                print("   -> Downloaded to device_runtime.log")
            except:
                print("   -> No runtime.log found.")
            
            try:
                scp.get(f"{REMOTE_APP_DIR}/{FOLDER_NAME}/settings.json", local_path="settings.json")
                print("   -> Downloaded to settings.json (preserved)")
                # Copy the preserved settings.json into the deploy directory so it gets pushed back
                os.system(f"cp settings.json deploy/{FOLDER_NAME}/settings.json")
            except:
                print("   -> No settings.json found on device.")
    except Exception as e:
        print(f"   -> Failed to fetch files: {e}")

    print("4) Removing old revision from SpruceOS...")
    target_folder = f"{REMOTE_APP_DIR}/{FOLDER_NAME}"
    ssh.exec_command(f"rm -rf '{target_folder}'")
    
    print("5) Pushing new application files via secure copy...")
    try:
        with SCPClient(ssh.get_transport()) as scp:
            scp.put(f"deploy/{FOLDER_NAME}", recursive=True, remote_path=REMOTE_APP_DIR)
    except Exception as e:
        print(f"[!] File stream interrupted: {e}")
        ssh.close()
        sys.exit(1)
        
    print("=========================================")
    print(" ✅ Push Complete! The app is updated.")
    print("=========================================")
    ssh.close()

if __name__ == '__main__':
    deploy()
