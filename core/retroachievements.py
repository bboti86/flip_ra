import urllib.request
import urllib.parse
import urllib.error
import json
import os

import time

CACHE_FILE = os.path.join(os.path.dirname(__file__), '..', 'api_cache.json')
CACHE_TTL = 3600  # 1 hour

def _load_cache():
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _save_cache(cache):
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f)
    except Exception as e:
        print(f"[ERROR] Failed to save cache: {e}")

def _get_cached_data(key):
    cache = _load_cache()
    if key in cache:
        entry = cache[key]
        if time.time() - entry.get("timestamp", 0) < CACHE_TTL:
            return entry.get("data")
    return None

def _set_cached_data(key, data):
    cache = _load_cache()
    cache[key] = {
        "timestamp": time.time(),
        "data": data
    }
    _save_cache(cache)


def verify_credentials(username, password):
    """
    Checks if username and password/api_key are valid via RetroAchievements Web API.
    A simple call to GetUserSummary is sufficient.
    """
    if not username or not password:
        return False, "Missing credentials"
        
    # Always fetch fresh auth to ensure credentials are correct, but cache the details!
    url = f"https://retroachievements.org/API/API_GetUserSummary.php?u={username}&y={password}&user={username}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                if "error" in data:
                    return False, data["error"]
                
                # Cache the summary since it contains rank and points!
                _set_cached_data("summary", data)
                return True, "Success"
            return False, f"HTTP error {response.status}"
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return False, "Invalid Username or Web API Key!"
        return False, f"RetroAchievements HTTP Error {e.code}"
    except Exception as e:
        print(f"[ERROR] API Exception: {e}")
        return False, f"Connection failed. Wi-Fi?"

def get_recent_achievements(username, password, count=10080):
    """
    Fetches the recently earned achievements for the user.
    """
    if not username or not password:
        return []
        
    cached = _get_cached_data("recent")
    if cached is not None:
        return cached

    url = f"https://retroachievements.org/API/API_GetUserRecentAchievements.php?u={username}&y={password}&m={count}&user={username}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                _set_cached_data("recent", data)
                return data
    except Exception as e:
        print(f"[ERROR] Fetch achievements failed: {e}")
    return []

def get_user_stats(username, password):
    """
    Returns high-level stats: Rank, Softcore/Hardcore Points, and Rarest Achievement.
    """
    stats = {
        "Rank": "Unknown",
        "TotalPoints": 0,
        "TotalTruePoints": 0,  # Hardcore points usually
        "HighestRatioAch": None
    }
    
    # 1. Get Summary Data (Hopefully cached by verify/auth run)
    summary = _get_cached_data("summary")
    if not summary:
        success, msg = verify_credentials(username, password)
        if success:
            summary = _get_cached_data("summary")
            
    if summary:
        stats["Rank"] = summary.get("Rank", "Unknown")
        stats["TotalPoints"] = int(summary.get("TotalPoints", 0))
        stats["TotalTruePoints"] = int(summary.get("TotalTruePoints", 0))
        
    # 2. Get Recent for Rarest
    recent = get_recent_achievements(username, password)
    if recent:
        rarest = None
        highest_ratio = -1
        for ach in recent:
            hr = float(ach.get("HardcoreRetroRatio", ach.get("RetroRatio", 0)))
            if hr > highest_ratio:
                highest_ratio = hr
                rarest = ach
        stats["HighestRatioAch"] = rarest
        
    return stats

def update_single_config(cfg_path, username, password, prefs):
    """Internal helper to update a single config file with credentials and preferences."""
    if not os.path.exists(cfg_path):
        return False, "File not found"
        
    try:
        with open(cfg_path, 'r') as f:
            lines = f.readlines()
            
        new_lines = []
        # Track which keys we've updated
        handled_keys = set()
        
        # Credentials and fixed overrides
        overrides = {
            'cheevos_username': f'"{username}"',
            'cheevos_password': f'"{password}"',
            'cheevos_token': '""',
            'cheevos_enable': '"true"'
        }
        # Merge theme preferences (converted to RA format strings)
        for k, v in prefs.items():
            if isinstance(v, bool):
                overrides[k] = '"true"' if v else '"false"'
            else:
                overrides[k] = f'"{v}"'
        
        for line in lines:
            stripped = line.strip()
            found_match = False
            for key in overrides:
                if stripped.startswith(key):
                    new_lines.append(f'{key} = {overrides[key]}\n')
                    handled_keys.add(key)
                    found_match = True
                    break
            
            if not found_match:
                new_lines.append(line)
                
        # Append anything that wasn't already in the file
        for key, val in overrides.items():
            if key not in handled_keys:
                new_lines.append(f'{key} = {val}\n')
            
        with open(cfg_path, 'w') as f:
            f.writelines(new_lines)
        return True, "Updated"
    except Exception as e:
        return False, str(e)

def update_retroarch_config(username, password, prefs):
    cfg_paths = [
        '/mnt/SDCARD/RetroArch/retroarch.cfg',
        '/mnt/SDCARD/RetroArch/platform/retroarch-A30.cfg',
        '/mnt/SDCARD/RetroArch/platform/retroarch-Brick.cfg',
        '/mnt/SDCARD/RetroArch/platform/retroarch-Flip.cfg',
        '/mnt/SDCARD/RetroArch/platform/retroarch-SmartPro.cfg',
        '/mnt/SDCARD/RetroArch/platform/retroarch-SmartProS.cfg',
        '/mnt/SDCARD/RetroArch/platform/retroarch-Pixel2.cfg'
    ]
    
    updated_count = 0
    errors = []
    
    for path in cfg_paths:
        if os.path.exists(path):
            success, msg = update_single_config(path, username, password, prefs)
            if success:
                updated_count += 1
                print(f"[DEBUG] Successfully updated: {path}")
            else:
                errors.append(f"{path}: {msg}")
                print(f"[ERROR] Failed to update {path}: {msg}")
    
    # Fallback for local testing
    if updated_count == 0:
        test_path = 'test_retroarch.cfg'
        if not os.path.exists(test_path):
            with open(test_path, 'w') as f: f.write("")
        update_single_config(test_path, username, password, prefs)
        print(f"[DEBUG] No system configs found, updated local {test_path}")
        return True, "Updated local test config"

    if errors and updated_count == 0:
        return False, "; ".join(errors)
        
    return True, f"Updated {updated_count} config files"

def get_game_list(username, api_key, console_id):
    """
    Fetches the list of games for a specific console ID.
    """
    cache_key = f"console_{console_id}_games"
    cached = _get_cached_data(cache_key)
    if cached:
        print(f"[CACHE] Hit for console {console_id} games")
        return cached

    print(f"[API] Fetching game list for console {console_id}")
    url = f"https://retroachievements.org/API/API_GetGameList.php?u={username}&y={api_key}&i={console_id}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                if isinstance(data, list):
                    _set_cached_data(cache_key, data)
                    return data
    except Exception as e:
        print(f"[ERROR] get_game_list failed: {e}")
    return []

def get_game_info_and_user_progress(username, api_key, game_id):
    """
    Gets detailed game info and user achievement progress for a game.
    """
    cache_key = f"game_{game_id}_progress"
    cached = _get_cached_data(cache_key)
    if cached:
        print(f"[CACHE] Hit for game {game_id} progress")
        return cached

    print(f"[API] Fetching progress for game {game_id}")
    url = f"https://retroachievements.org/API/API_GetGameInfoAndUserProgress.php?u={username}&y={api_key}&user={username}&g={game_id}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                _set_cached_data(cache_key, data)
                return data
    except Exception as e:
        print(f"[ERROR] get_game_info_and_user_progress failed: {e}")
    return {}

def download_badge(badge_name, is_locked=False):
    """
    Downloads a badge image if it doesn't exist locally.
    Returns the local path.
    """
    suffix = "_lock" if is_locked else ""
    local_filename = f"{badge_name}{suffix}.png"
    local_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'badges', local_filename)
    
    if os.path.exists(local_path):
        return local_path
        
    url = f"https://media.retroachievements.org/Badge/{badge_name}{suffix}.png"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                with open(local_path, 'wb') as f:
                    f.write(response.read())
                return local_path
    except Exception as e:
        print(f"[ERROR] download_badge failed ({url}): {e}")
    return None
