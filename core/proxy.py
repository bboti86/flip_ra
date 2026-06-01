import os
import sys
import time
import subprocess
from core.logger import setup_logger

logger = setup_logger("proxy")

# The RetroArch config paths used by flip_ra / Spruce OS
RETROARCH_CFG_PATHS = [
    '/mnt/SDCARD/RetroArch/retroarch.cfg',
    '/mnt/SDCARD/RetroArch/platform/retroarch-A30.cfg',
    '/mnt/SDCARD/RetroArch/platform/retroarch-Brick.cfg',
    '/mnt/SDCARD/RetroArch/platform/retroarch-Flip.cfg',
    '/mnt/SDCARD/RetroArch/platform/retroarch-SmartPro.cfg',
    '/mnt/SDCARD/RetroArch/platform/retroarch-SmartProS.cfg',
    '/mnt/SDCARD/RetroArch/platform/retroarch-Pixel2.cfg'
]

def is_proxy_running():
    """Checks if the proxy daemon is currently running by scanning /proc."""
    try:
        proc_path = '/proc'
        if not os.path.exists(proc_path):
            return False
            
        for pid_str in os.listdir(proc_path):
            if not pid_str.isdigit():
                continue
                
            cmdline_path = os.path.join(proc_path, pid_str, 'cmdline')
            try:
                with open(cmdline_path, 'rb') as f:
                    content = f.read()
                    
                args = [arg.decode('utf-8', errors='ignore') for arg in content.split(b'\x00') if arg]
                cmdline = ' '.join(args)
                
                if int(pid_str) == os.getpid():
                    continue
                    
                if 'raofflineproxy.main' in cmdline and 'run-service' in cmdline:
                    return True
            except (IOError, ValueError):
                continue
    except Exception as e:
        logger.error(f"Failed to check proxy status via /proc: {e}")
    return False

def check_config_state():
    """Verifies if the retroarch config is set to use the proxy."""
    existing_paths = [p for p in RETROARCH_CFG_PATHS if os.path.exists(p)]
    if not existing_paths:
        # Fallback for local testing
        if os.path.exists('test_retroarch.cfg'):
            existing_paths = ['test_retroarch.cfg']
        else:
            return False
            
    try:
        # Checking the first existing config is sufficient as they are kept in sync
        with open(existing_paths[0], 'r') as f:
            content = f.read()
            if 'cheevos_custom_host = "127.0.0.1:8080"' in content:
                return True
    except Exception as e:
        logger.error(f"Error reading config: {e}")
    return False

def get_proxy_state():
    """Returns True if the proxy is running and config is patched, False otherwise."""
    return is_proxy_running() and check_config_state()

def patch_retroarch_config(enable):
    """Patches the retroarch configuration to enable/disable the offline proxy."""
    existing_paths = [p for p in RETROARCH_CFG_PATHS if os.path.exists(p)]
    
    # Fallback for local testing
    if not existing_paths:
        test_path = 'test_retroarch.cfg'
        if not os.path.exists(test_path):
            with open(test_path, 'w') as f:
                f.write("")
        existing_paths = [test_path]
        
    success_count = 0
    for path in existing_paths:
        try:
            with open(path, 'r') as f:
                lines = f.readlines()
                
            new_lines = []
            host_patched = False
            enable_patched = False
            
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('cheevos_custom_host'):
                    if enable:
                        new_lines.append('cheevos_custom_host = "127.0.0.1:8080"\n')
                    else:
                        new_lines.append('cheevos_custom_host = ""\n')
                    host_patched = True
                elif stripped.startswith('cheevos_enable'):
                    if enable:
                        new_lines.append('cheevos_enable = "true"\n')
                    else:
                        new_lines.append(line)
                    enable_patched = True
                else:
                    new_lines.append(line)
                    
            if enable:
                if not host_patched:
                    new_lines.append('cheevos_custom_host = "127.0.0.1:8080"\n')
                if not enable_patched:
                    new_lines.append('cheevos_enable = "true"\n')
                    
            with open(path, 'w') as f:
                f.writelines(new_lines)
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to patch config at {path}: {e}")
            
    return success_count > 0

def start_proxy():
    """Starts the proxy daemon in the background using python3."""
    if is_proxy_running():
        return True
        
    bin_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bin'))
    main_py = os.path.join(bin_dir, 'raofflineproxy', 'main.py')
    
    if not os.path.exists(main_py):
        logger.error(f"Proxy main.py not found at {main_py}")
        return False
        
    try:
        existing_paths = [p for p in RETROARCH_CFG_PATHS if os.path.exists(p)]
        primary_cfg = existing_paths[0] if existing_paths else '/mnt/SDCARD/RetroArch/retroarch.cfg'
        
        env = os.environ.copy()
        env['PYTHONPATH'] = bin_dir + (os.pathsep + env['PYTHONPATH'] if 'PYTHONPATH' in env else '')
        env['RAOFFLINEPROXY_CONFIG_DIR'] = '/mnt/SDCARD/App/RA_Manager/data'
        env['RAOFFLINEPROXY_RETROARCH_CFG'] = primary_cfg
        env['RAOFFLINEPROXY_APP_VERSION'] = '1.3.0-alpha1'
        env['RAOFFLINEPROXY_CACHE_IMAGES'] = '0'
        
        log_dir = '/mnt/SDCARD/App/RA_Manager/data'
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'service.log')
        try:
            log_handle = open(log_file, 'a', encoding='utf-8')
        except Exception:
            log_handle = subprocess.DEVNULL

        subprocess.Popen(
            [sys.executable, '-m', 'raofflineproxy.main', 'run-service'],
            stdout=log_handle,
            stderr=log_handle,
            stdin=subprocess.DEVNULL,
            env=env,
            start_new_session=True
        )
            
        logger.info(f"Proxy daemon started via {sys.executable} (logging to {log_file})")
        return True
    except Exception as e:
        logger.error(f"Failed to start proxy: {e}")
        return False

def stop_proxy():
    """Kills the proxy daemon."""
    try:
        subprocess.run(['pkill', '-f', 'raofflineproxy.main'])
        logger.info("Proxy daemon stopped")
        return True
    except Exception as e:
        logger.error(f"Failed to stop proxy: {e}")
        return False

def toggle_proxy():
    """Toggles the proxy state and returns the actual resulting state."""
    current_state = get_proxy_state()
    new_state = not current_state
    
    config_patched = patch_retroarch_config(new_state)
    
    if new_state:
        start_proxy()
    else:
        stop_proxy()
        
    time.sleep(0.3)  # Give the daemon a moment to initialize/stop
    return get_proxy_state()
