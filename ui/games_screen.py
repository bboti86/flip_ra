import sdl2
import sdl2.ext
import json
import os
import threading
import difflib
import time
from .components import render_text, draw_image
from core import input, retroachievements, hltb

# Mapping SpruceOS system names to RA Console IDs
SYSTEM_MAP = {
    "ARCADE": 27,
    "SFC": 3,
    "SNES": 3,
    "GBA": 5,
    "GB": 4,
    "GBC": 6,
    "MD": 1,
    "GENESIS": 1,
    "FC": 7,
    "NES": 7,
    "PS": 12,
    "PSX": 12,
    "N64": 2,
    "NDS": 18,
    "PSP": 41,
    "PCE": 8,
    "TG16": 8
}

class GamesScreen:
    def __init__(self, renderer, font):
        self.renderer = renderer
        self.font = font
        self.config_path = os.path.join(os.path.dirname(__file__), '..', 'settings.json')
        # On device: /mnt/SDCARD/Saves/pyui-favorites.json
        # Locally for testing: ./pyui-favorites.json
        self.favorites_path = "/mnt/SDCARD/Saves/pyui-favorites.json"
        if not os.path.exists(self.favorites_path):
            self.favorites_path = "pyui-favorites.json"
            
        self.load_config()
        self.username = self.config.get("ra_username", "")
        self.api_key = self.config.get("ra_api_key", "")
        
        # States: 0: Game Selection, 1: Loading/Matching, 2: Downloading Images, 3: Achievement Viewer
        self.state = 0
        self.favorites = []
        self.selected_game_idx = 0
        self.scroll_index = 0
        
        # State Data
        self.target_game = None
        self.ra_game_id = None
        self.game_data = {}
        self.achievements = []
        self.download_queue = []
        self.total_downloads = 0
        self.download_progress = 0
        
        self.error_msg = None
        self.loading_msg = ""
        
        self.hltb_data = None
        self.sort_mode = "DEFAULT" # DEFAULT or SHORTEST
        self.load_favorites()

    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except:
            self.config = {}

    def load_favorites(self):
        try:
            if os.path.exists(self.favorites_path):
                print(f"[INFO] Loading favorites from {self.favorites_path}")
                with open(self.favorites_path, 'r') as f:
                    self.favorites = json.load(f)
                print(f"[INFO] Loaded {len(self.favorites)} favorite games")
                self.apply_sorting()
            else:
                self.error_msg = "No favorites found on device."
        except Exception as e:
            self.error_msg = f"Error loading favorites: {e}"

    def apply_sorting(self):
        if self.sort_mode == "SHORTEST":
            print("[INFO] Sorting favorites by HLTB Main Story time...")
            # We need to pre-fetch or use cached times if available
            def get_sort_time(g):
                # Try cache first
                data = hltb.get_game_times(g["display_name"])
                return data["main"] if data else 999
            self.favorites.sort(key=get_sort_time)
        else:
            # Re-load from file for default order
            try:
                with open(self.favorites_path, 'r') as f:
                    self.favorites = json.load(f)
            except: pass

    def start_matching(self):
        self.state = 1
        self.error_msg = None
        self.loading_msg = f"Matching {self.target_game['display_name']}..."
        
        def _task():
            try:
                system_name = self.target_game.get("game_system_name", "").upper()
                console_id = SYSTEM_MAP.get(system_name)
                
                if not console_id:
                    self.error_msg = f"System {system_name} not supported by RA."
                    self.state = 0
                    return

                # Get game list for console to match ID
                game_list = retroachievements.get_game_list(self.username, self.api_key, console_id)
                if not game_list:
                    self.error_msg = "Could not fetch games from RA."
                    self.state = 0
                    return
                
                # Fuzzy matching
                titles = [g["Title"] for g in game_list]
                matches = difflib.get_close_matches(self.target_game["display_name"], titles, n=1, cutoff=0.3)
                
                if not matches:
                    self.error_msg = "No matching game found on RA."
                    self.state = 0
                    return
                
                matched_title = matches[0]
                self.ra_game_id = next(g["ID"] for g in game_list if g["Title"] == matched_title)
                print(f"[INFO] Matched game: '{self.target_game['display_name']}' -> '{matched_title}' (ID: {self.ra_game_id})")
                
                self.loading_msg = f"Found: {matched_title}. Loading progress..."
                self.fetch_game_progress()
                
            except Exception as e:
                self.error_msg = f"Matching failed: {e}"
                self.state = 0
                
        threading.Thread(target=_task, daemon=True).start()

    def fetch_game_progress(self):
        data = retroachievements.get_game_info_and_user_progress(self.username, self.api_key, self.ra_game_id)
        if not data:
            self.error_msg = "Failed to fetch achievement details."
            self.state = 0
            return
            
        self.game_data = data
        self.hltb_data = None
        raw_achs = data.get("Achievements", {})
        # Dict to sorted list
        self.achievements = sorted(raw_achs.values(), key=lambda x: x.get("DisplayOrder", 0))
        self.scroll_index = 0
        print(f"[INFO] Loaded {len(self.achievements)} achievements for game ID {self.ra_game_id}")
        
        # Start background HLTB fetch
        def _hltb_task():
            title = self.game_data.get("Title")
            year = self.game_data.get("Released")
            self.hltb_data = hltb.get_game_times(title, year)
            if self.hltb_data:
                print(f"[HLTB] Found data: {self.hltb_data}")
        threading.Thread(target=_hltb_task, daemon=True).start()
        
        # Build download queue
        self.download_queue = []
        badges_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'badges')
        if not os.path.exists(badges_dir):
            os.makedirs(badges_dir)
            print(f"[INFO] Created badges directory: {badges_dir}")

        for ach in self.achievements:
            badge = ach.get("BadgeName")
            is_unlocked = "DateEarned" in ach or "DateEarnedHardcore" in ach
            
            # Check for regular badge
            local_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'badges', f"{badge}.png")
            if not os.path.exists(local_path):
                self.download_queue.append((badge, False))
                
            # Check for lock badge
            local_lock_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'badges', f"{badge}_lock.png")
            if not os.path.exists(local_lock_path):
                self.download_queue.append((badge, True))
        
        if self.download_queue:
            print(f"[INFO] Found {len(self.download_queue)} missing badges, starting download...")
            self.total_downloads = len(self.download_queue)
            self.download_progress = 0
            self.state = 2
            self.start_downloading()
        else:
            print("[INFO] All badges cached locally, skipping download.")
            self.state = 3

    def start_downloading(self):
        def _task():
            for i, (badge, is_lock) in enumerate(self.download_queue):
                retroachievements.download_badge(badge, is_lock)
                self.download_progress = i + 1
                # Small sleep to be nice to API
                time.sleep(0.05)
            self.state = 3
            
        threading.Thread(target=_task, daemon=True).start()

    def handle_event(self, event):
        action = input.map_event(event)
        
        if self.state == 0: # Selection
            if action == input.L_BUMPER:
                return "SWITCH_TO_SETTINGS"
            elif action == input.R_BUMPER:
                return "SWITCH_TO_STATS"
            elif action == input.UP:
                self.selected_game_idx = max(0, self.selected_game_idx - 1)
            elif action == input.DOWN:
                self.selected_game_idx = min(len(self.favorites) - 1, self.selected_game_idx + 1)
            elif action == input.ACCEPT:
                if self.favorites:
                    self.target_game = self.favorites[self.selected_game_idx]
                    self.start_matching()
            elif action == input.CANCEL:
                return "SWITCH_TO_AUTH"
            elif action == input.SELECT:
                self.sort_mode = "SHORTEST" if self.sort_mode == "DEFAULT" else "DEFAULT"
                self.apply_sorting()
                self.selected_game_idx = 0
                
        elif self.state == 3: # Achievement Viewer
            if action == input.UP:
                self.scroll_index = max(0, self.scroll_index - 1)
            elif action == input.DOWN:
                if self.achievements:
                    self.scroll_index = min(len(self.achievements) - 5, self.scroll_index + 1)
                    if self.scroll_index < 0: self.scroll_index = 0
            elif action == input.CANCEL:
                self.state = 0
                self.scroll_index = 0
        
        return None

    def _draw_progress_bar(self, x, y, w, h, pct, color):
        self.renderer.fill((x, y, w, h), sdl2.ext.Color(50, 50, 50))
        self.renderer.fill((x, y, int(w * pct), h), sdl2.ext.Color(*color))

    def _draw_ascii_progress(self):
        # Center box
        cx, cy = 320, 240
        w, h = 400, 150
        self.renderer.fill((cx - w//2, cy - h//2, w, h), sdl2.ext.Color(20, 20, 30, 230))
        
        pct = self.download_progress / self.total_downloads if self.total_downloads > 0 else 0
        bar_len = 20
        filled = int(bar_len * pct)
        bar_str = "[" + "=" * filled + "." * (bar_len - filled) + "]"
        
        # Draw ASCII style
        render_text(self.renderer, self.font, "------------------------------", cx, cy - 50, (0, 255, 0), center=True)
        render_text(self.renderer, self.font, "   SYNCING BADGES FROM RA     ", cx, cy - 25, (0, 255, 0), center=True)
        render_text(self.renderer, self.font, f"   {bar_str} {int(pct*100)}%   ", cx, cy + 5, (0, 255, 0), center=True)
        render_text(self.renderer, self.font, f"   {self.download_progress} / {self.total_downloads} Files         ", cx, cy + 30, (0, 255, 0), center=True)
        render_text(self.renderer, self.font, "------------------------------", cx, cy + 55, (0, 255, 0), center=True)

    def draw(self):
        if self.state == 0: # Selection
            render_text(self.renderer, self.font, "Pick a Favorite Game", 320, 20, (255, 255, 255), center=True)
            if self.error_msg:
                render_text(self.renderer, self.font, self.error_msg, 320, 50, (255, 100, 100), center=True)
            
            # Draw list
            y_start = 80
            visible_count = 8
            start_off = max(0, self.selected_game_idx - visible_count // 2)
            
            for i in range(start_off, min(len(self.favorites), start_off + visible_count)):
                game = self.favorites[i]
                y = y_start + (i - start_off) * 45
                color = (255, 255, 100) if i == self.selected_game_idx else (200, 200, 200)
                prefix = "> " if i == self.selected_game_idx else "  "
                render_text(self.renderer, self.font, prefix + game["display_name"], 50, y, color)
                render_text(self.renderer, self.font, f"[{game.get('game_system_name', '??')}]", 500, y, (150, 150, 150))

            sort_hint = "Default" if self.sort_mode == "DEFAULT" else "Shortest (HLTB)"
            render_text(self.renderer, self.font, f"Sort: {sort_hint} (SELECT to toggle)", 320, 430, (150, 150, 255), center=True)
            render_text(self.renderer, self.font, "L1/R1: Tab | D-Pad: Select | A: Achievements", 320, 455, (150, 150, 150), center=True)

        elif self.state == 1: # Loading
            render_text(self.renderer, self.font, "Establishing Link...", 320, 220, (200, 200, 100), center=True)
            render_text(self.renderer, self.font, self.loading_msg, 320, 260, (255, 255, 255), center=True)

        elif self.state == 2: # Downloading
            if self.total_downloads > 10:
                self._draw_ascii_progress()
            else:
                render_text(self.renderer, self.font, f"Caching Images... ({self.download_progress}/{self.total_downloads})", 320, 240, (200, 200, 100), center=True)

        elif self.state == 3: # Viewer
            # Top Stats Section
            self.renderer.fill((0, 0, 640, 80), sdl2.ext.Color(30, 30, 40))
            render_text(self.renderer, self.font, self.game_data.get("Title", "Achievements"), 320, 10, (255, 255, 100), center=True)
            
            unlocked = int(self.game_data.get("NumAwardedToUser", 0))
            total = int(self.game_data.get("NumAchievements", 0))
            pct = unlocked / total if total > 0 else 0
            
            render_text(self.renderer, self.font, f"Completion: {unlocked}/{total} ({int(pct*100)}%)", 320, 35, (255, 255, 255), center=True)
            self._draw_progress_bar(120, 60, 400, 10, pct, (0, 255, 0))
            
            # HLTB Times
            if self.hltb_data:
                h = self.hltb_data
                hltb_str = f"Story: {h['main']}h | Extras: {h['plus']}h | 100%: {h['100']}h"
                render_text(self.renderer, self.font, hltb_str, 320, 75, (200, 200, 255), center=True)
            
            # List achievements (show exactly 5)
            for i in range(5):
                idx = self.scroll_index + i
                if idx >= len(self.achievements): break
                
                ach = self.achievements[idx]
                y = 100 + (i * 70)
                
                is_unlocked = "DateEarned" in ach or "DateEarnedHardcore" in ach
                badge_name = ach.get("BadgeName")
                suffix = "" if is_unlocked else "_lock"
                local_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'badges', f"{badge_name}{suffix}.png")
                
                # Draw Icon
                draw_image(self.renderer, local_path, 20, y, 64, 64)
                
                # Draw Text
                title_color = (255, 255, 255) if is_unlocked else (150, 150, 150)
                desc_color = (180, 180, 180) if is_unlocked else (100, 100, 100)
                
                render_text(self.renderer, self.font, ach.get("Title", "???"), 100, y, title_color)
                render_text(self.renderer, self.font, ach.get("Description", ""), 100, y + 25, desc_color)
                
                points = ach.get("Points", 0)
                render_text(self.renderer, self.font, f"{points} pts", 540, y, (150, 255, 150))

            render_text(self.renderer, self.font, "D-Pad: Scroll | B: Back to Games", 320, 450, (150, 150, 150), center=True)
