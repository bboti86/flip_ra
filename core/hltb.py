import urllib.request
import urllib.parse
import urllib.error
import json
import os
import re
import time

CACHE_FILE = "/mnt/SDCARD/Saves/hltb_cache.json"
if not os.path.exists("/mnt/SDCARD/Saves"):
    CACHE_FILE = "hltb_cache.json"

class HLTB:
    def __init__(self):
        self.base_url = "https://howlongtobeat.com"
        # Standard desktop user agent to avoid bot detection
        self.user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.cache = self._load_cache()
        
        self.auth_token = None
        self.hp_key = None
        self.hp_val = None
        self.search_path = None
        self.last_discovery = 0

    def _load_cache(self):
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}

    def _save_cache(self):
        try:
            with open(CACHE_FILE, 'w') as f:
                json.dump(self.cache, f)
        except:
            pass

    def _discover(self):
        """
        Scans HLTB homepage script chunks to find the current active API prefix.
        Then calls the /init endpoint to get session tokens.
        """
        if time.time() - self.last_discovery < 1800 and self.auth_token:
            return True

        print("[HLTB] Discovering API parameters...")
        try:
            # 1. Fetch main page to find JS chunks
            req = urllib.request.Request(self.base_url, headers={'User-Agent': self.user_agent})
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8')
                
            # 2. Extract and scan scripts
            scripts = re.findall(r'/_next/static/chunks/([a-zA-Z0-9.\-_]+)\.js', html)
            print(f"[HLTB] Found {len(scripts)} script chunks.")
            
            discovered_path = None
            for script in scripts:
                if len(script) < 8: continue
                
                js_url = f"{self.base_url}/_next/static/chunks/{script}.js"
                try:
                    js_req = urllib.request.Request(js_url, headers={'User-Agent': self.user_agent})
                    with urllib.request.urlopen(js_req, timeout=5) as js_response:
                        content = js_response.read().decode('utf-8')
                        
                        # Look for POST fetch to /api/
                        path_match = re.search(r'["\'](/api/(?:find|s|search)/[a-zA-Z0-9]+)["\']', content)
                        if not path_match:
                             path_match = re.search(r'concat\("(/api/(?:find|s|search)/[a-zA-Z0-9]+)"\)', content)
                        
                        if path_match:
                            discovered_path = path_match.group(1)
                            print(f"[HLTB] Discovered search path in {script}: {discovered_path}")
                            break
                except:
                    continue
            
            self.search_path = discovered_path or "/api/find" # Fallback
            print(f"[HLTB] Using search path: {self.search_path}")

            # 3. Fetch Handshake tokens
            init_url = f"{self.base_url}{self.search_path}/init?t={int(time.time() * 1000)}"
            init_req = urllib.request.Request(init_url, headers={
                'User-Agent': self.user_agent,
                'Referer': self.base_url + '/'
            })
            with urllib.request.urlopen(init_req, timeout=10) as response:
                init_data = json.loads(response.read().decode('utf-8'))
                self.auth_token = init_data.get("token")
                # Find hpKey/hpVal
                self.hp_key = init_data.get("hpKey")
                self.hp_val = init_data.get("hpVal")
                
                # Dynamic fallback for key names
                if not self.hp_key:
                    for k, v in init_data.items():
                        if "key" in k.lower(): self.hp_key = v
                        if "val" in k.lower(): self.hp_val = v
                
                if not self.hp_key: # Last resort: pick non-token strings
                    for k, v in init_data.items():
                        if k != "token" and isinstance(v, str):
                            if not self.hp_key: self.hp_key = k; self.hp_val = v
                            else: break 

            self.last_discovery = time.time()
            return True
        except Exception as e:
            print(f"[HLTB] Discovery failed: {e}")
            return False

    def search(self, game_title, release_year=None):
        cache_key = f"{game_title}_{release_year}" if release_year else game_title
        if cache_key in self.cache:
            return self.cache[cache_key]

        if not self._discover():
            return None

        url = self.base_url + self.search_path
        
        # Build payload with dynamic challenge
        payload = {
            "searchType": "games",
            "searchTerms": [t for t in game_title.split(" ") if t],
            "searchPage": 1,
            "size": 20,
            "searchOptions": {
                "games": {
                    "userId": 0,
                    "platform": "",
                    "sortCategory": "popular",
                    "rangeCategory": "main",
                    "rangeTime": {"min": None, "max": None},
                    "gameplay": {"perspective": "", "flow": "", "genre": ""},
                    "rangeYear": {"min": "", "max": ""},
                    "modifier": ""
                },
                "users": {"searchAlgorithm": "proximity"},
                "lists": {"sortCategory": "follows"},
                "filter": "",
                "sort": 0,
                "randomizer": 0
            },
            "useCache": True,
            self.hp_key: self.hp_val # Mandatory challenge
        }
        
        if release_year:
            payload["searchOptions"]["games"]["rangeYear"]["min"] = str(release_year)
            payload["searchOptions"]["games"]["rangeYear"]["max"] = str(release_year)

        data = json.dumps(payload).encode('utf-8')
        headers = {
            'User-Agent': self.user_agent,
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Origin': self.base_url,
            'Referer': self.base_url + '/',
            'x-auth-token': self.auth_token,
            'x-hp-key': self.hp_key,
            'x-hp-val': self.hp_val
        }

        try:
            req = urllib.request.Request(url, data=data, headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=15) as response:
                result = json.loads(response.read().decode('utf-8'))
                
            if result and 'data' in result and len(result['data']) > 0:
                best_hit = result['data'][0]
                times = {
                    "main": round(best_hit.get("comp_main", 0) / 3600, 1),
                    "plus": round(best_hit.get("comp_plus", 0) / 3600, 1),
                    "100": round(best_hit.get("comp_100", 0) / 3600, 1),
                    "title": best_hit.get("game_name"),
                    "hltb_id": best_hit.get("game_id")
                }
                self.cache[cache_key] = times
                self._save_cache()
                return times
        except urllib.error.HTTPError as e:
            if e.code in [403, 308, 404]:
                print(f"[HLTB] Search blocked ({e.code}), resetting...")
                self.last_discovery = 0
            else:
                print(f"[HLTB] Search failed for {game_title}: {e}")
        except Exception as e:
            print(f"[HLTB] Search error for {game_title}: {e}")
            
        return None

# Global instance
client = HLTB()

def get_game_times(title, year=None):
    return client.search(title, year)
