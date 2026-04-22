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

# ANSI Color Codes
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

def create_ssh_client(server, port, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password)
    return client

def run_local_build():
    print(f"\n{BOLD}{CYAN}1) 🛠️  Re-building deployment...{RESET}")
    print(f"{BOLD}{BLUE}Cleaning old deployment...{RESET}")
    os.system("rm -rf deploy")
    
    print(f"{BOLD}{BLUE}Creating new deployment directory at 'deploy/RA_Manager'...{RESET}")
    os.system("mkdir -p deploy/RA_Manager")
    
    print(f"{BOLD}{BLUE}Copying application files...{RESET}")
    # Copy code and libs, but skip heavy assets subfolders
    os.system("cp -r core ui libs deploy/RA_Manager/ 2>/dev/null || true")
    os.system("cp main.py launch.sh settings.json config.json icon.png deploy/RA_Manager/ 2>/dev/null || true")
    
    # Only copy static assets (fonts, etc) but skip the downloaded badge/icon folders
    os.system("mkdir -p deploy/RA_Manager/assets")
    os.system("cp assets/*.png assets/*.ttf deploy/RA_Manager/assets/ 2>/dev/null || true")
    
    print(f"{BOLD}{BLUE}Cleaning up __pycache__ directories from deployment...{RESET}")
    os.system("find deploy/RA_Manager -type d -name '__pycache__' -exec rm -r {} + 2>/dev/null || true")

def deploy():
    os.system('clear')
    run_local_build()
    print(f"{BOLD}{GREEN}=================================================={RESET}")
    print(f" {GREEN}✅ Deployment Complete! The app is ready to push.{RESET}")
    print(f"{BOLD}{GREEN}=================================================={RESET}")
    
    print(f"{BOLD}{CYAN}2) 🤝 Connecting to {DEVICE_IP} as {USER}...{RESET}")
    try:
        ssh = create_ssh_client(DEVICE_IP, 22, USER, PASSWORD)
    except Exception as e:
        print(f"{RED}[!] ❌ Failed to connect: {e}{RESET}")
        sys.exit(1)

    print(f"{BOLD}{CYAN}3) 📥 Grabbing runtime logs, badges cache, and settings.json from device...{RESET}")
    try:
        with SCPClient(ssh.get_transport()) as scp:
            # Grab rotated logs
            for log_suffix in ["", ".1", ".2"]:
                remote_log = f"{REMOTE_APP_DIR}/{FOLDER_NAME}/runtime.log{log_suffix}"
                local_log = f"device_runtime.log{log_suffix}"
                try:
                    scp.get(remote_log, local_path=local_log)
                    print(f"   {BLUE}-> 📄 Downloaded {os.path.basename(remote_log)} to {local_log}{RESET}")
                except:
                    pass
            
            # Grab caches (Settings, Match, API) to keep your PC in sync if needed, 
            # but we won't strictly need them for the push anymore since we aren't deleting them on device.
            for filename in ["settings.json", "match_cache.json", "api_cache.json"]:
                remote_path = f"{REMOTE_APP_DIR}/{FOLDER_NAME}/{filename}"
                try:
                    scp.get(remote_path, local_path=filename)
                    print(f"   {BLUE}-> ⚙️  Syncing {filename} to local PC{RESET}")
                except:
                    pass

    except Exception as e:
        print(f"   {RED}-> ❌ Failed to fetch files: {e}{RESET}")

    print(f"{BOLD}{CYAN}4) 🧹 Cleaning code from device (preserving assets and caches)...{RESET}")
    target_folder = f"{REMOTE_APP_DIR}/{FOLDER_NAME}"
    # Explicitly remove code folders but keep assets/ and .json files
    ssh.exec_command(f"rm -rf {target_folder}/core {target_folder}/ui {target_folder}/libs {target_folder}/main.py")
    stdout.channel.recv_exit_status()
    
    print(f"{BOLD}{CYAN}5) 🚀 Pushing new application files via secure copy...{RESET}")
    try:
        with SCPClient(ssh.get_transport()) as scp:
            scp.put(f"deploy/{FOLDER_NAME}", recursive=True, remote_path=REMOTE_APP_DIR)
    except Exception as e:
        print(f"{RED}[!] ❌ File stream interrupted: {e}{RESET}")
        ssh.close()
        sys.exit(1)
        
    print(f"\n{BOLD}{GREEN}========================================={RESET}")
    print(f" {BOLD}{GREEN}🏁 ✅ Push Complete! The app is updated.{RESET}")
    print(f"{BOLD}{GREEN}========================================={RESET}\n")
    ssh.close()

if __name__ == '__main__':
    deploy()
