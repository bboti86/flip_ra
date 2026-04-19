import sdl2
import sdl2.ext
import json
import os
import threading
import difflib
import time
from .components import render_text, draw_image, render_text_shadow, draw_panel, draw_selector
# from core import hltb
from core import input, retroachievements

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
        
        # Global Sync State
        self.sync_current_game_name = ""
        self.sync_current_idx = 0
        self.sync_total_games = 0
        self.sync_download_progress = 0
        self.sync_total_downloads = 0
        self.sync_cancel = False
        
        self.error_msg = None
        self.loading_msg = ""
        
        self.hltb_data = None
        self.sort_mode = "DEFAULT" # DISABLED: "SHORTEST"
        self.load_favorites()
        
        # Navigation Repeat Logic
        self.repeat_timers = {} # action -> elapsed_time
        self.REPEAT_DELAY = 0.4
        self.REPEAT_INTERVAL = 0.08
        self.PAGE_REPEAT_INTERVAL = 0.15

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
        # DISABLED: HLTB Sorting
        if self.sort_mode == "SHORTEST":
            # print("[INFO] Sorting favorites by HLTB Main Story time...")
            # def get_sort_time(g):
            #     data = hltb.get_game_times(g["display_name"])
            #     return data["main"] if data else 999
            # self.favorites.sort(key=get_sort_time)
            pass
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
                matched_game = next(g for g in game_list if g["Title"] == matched_title)
                self.ra_game_id = matched_game["ID"]
                
                icon_url = matched_game.get("ImageIcon")
                if icon_url:
                    retroachievements.download_game_icon(icon_url, self.target_game["display_name"])
                print(f"[INFO] Matched game: '{self.target_game['display_name']}' -> '{matched_title}' (ID: {self.ra_game_id})")
                
                self.loading_msg = f"Found: {matched_title}. Loading progress..."
                self.fetch_game_progress()
                
            except Exception as e:
                self.error_msg = f"Matching failed: {e}"
                self.state = 0
                
        threading.Thread(target=_task, daemon=True).start()

    def start_global_sync(self):
        self.state = 4
        self.sync_cancel = False
        self.sync_total_games = len(self.favorites)
        self.sync_current_idx = 0
        self.sync_download_progress = 0
        self.sync_total_downloads = 0
        self.error_msg = None
        
        def _task():
            badges_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'badges')
            if not os.path.exists(badges_dir):
                os.makedirs(badges_dir)
                
            total_dl = 0
            for i, game in enumerate(self.favorites):
                if self.sync_cancel: break
                self.sync_current_idx = i + 1
                self.sync_current_game_name = game["display_name"]
                
                # Matching
                system_name = game.get("game_system_name", "").upper()
                console_id = SYSTEM_MAP.get(system_name)
                if not console_id: continue
                
                game_list = retroachievements.get_game_list(self.username, self.api_key, console_id)
                if not game_list: continue
                
                titles = [g["Title"] for g in game_list]
                matches = difflib.get_close_matches(game["display_name"], titles, n=1, cutoff=0.3)
                if not matches: continue
                
                matched_game = next(g for g in game_list if g["Title"] == matches[0])
                ra_game_id = matched_game["ID"]
                
                icon_url = matched_game.get("ImageIcon")
                if icon_url:
                    retroachievements.download_game_icon(icon_url, game["display_name"])
                
                # Fetch progress
                data = retroachievements.get_game_info_and_user_progress(self.username, self.api_key, ra_game_id)
                if not data: continue
                
                raw_achs = data.get("Achievements", {})
                
                # Collect missing
                missing = []
                for ach in raw_achs.values():
                    badge = ach.get("BadgeName")
                    if not badge: continue
                    if not os.path.exists(os.path.join(badges_dir, f"{badge}.png")):
                        missing.append((badge, False))
                    if not os.path.exists(os.path.join(badges_dir, f"{badge}_lock.png")):
                        missing.append((badge, True))
                        
                self.sync_total_downloads += len(missing)
                
                for b, is_lock in missing:
                    if self.sync_cancel: break
                    retroachievements.download_badge(b, is_lock)
                    self.sync_download_progress += 1
                    total_dl += 1
                    time.sleep(0.05)
                    
            # Done
            self.state = 0
            if total_dl > 0:
                self.error_msg = f"Synced {total_dl} new badges!"
            elif not self.sync_cancel:
                self.error_msg = "All badges already cached!"

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
        
        # Start background HLTB fetch - DISABLED
        # def _hltb_task():
        #     title = self.game_data.get("Title")
        #     year = self.game_data.get("Released")
        #     self.hltb_data = hltb.get_game_times(title, year)
        #     if self.hltb_data:
        #         print(f"[HLTB] Found data: {self.hltb_data}")
        # threading.Thread(target=_hltb_task, daemon=True).start()
        
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

    def update(self, dt):
        if self.state not in [0, 3]:
            return

        for action in [input.UP, input.DOWN, input.PAGE_UP, input.PAGE_DOWN]:
            if input.is_pressed(action):
                if action not in self.repeat_timers:
                    # Initial press already handled by handle_event
                    self.repeat_timers[action] = 0.0
                else:
                    self.repeat_timers[action] += dt
                    
                    delay = self.REPEAT_DELAY
                    interval = self.PAGE_REPEAT_INTERVAL if "PAGE" in action else self.REPEAT_INTERVAL
                    
                    if self.repeat_timers[action] >= delay:
                        # Perform repeated navigation
                        self._navigate(action)
                        # Reset to delay so it triggers again after 'interval'
                        self.repeat_timers[action] = delay - interval
            else:
                # Button released
                if action in self.repeat_timers:
                    del self.repeat_timers[action]

    def _navigate(self, action):
        if self.state == 0: # Selection
            count = len(self.favorites)
            if count == 0: return
            
            if action == input.UP:
                self.selected_game_idx = (self.selected_game_idx - 1) % count
            elif action == input.DOWN:
                self.selected_game_idx = (self.selected_game_idx + 1) % count
            elif action == input.PAGE_UP:
                self.selected_game_idx = max(0, self.selected_game_idx - 8)
            elif action == input.PAGE_DOWN:
                self.selected_game_idx = min(count - 1, self.selected_game_idx + 8)

        elif self.state == 3: # Achievement Viewer
            count = len(self.achievements)
            if count == 0: return
            max_scroll = max(0, count - 5)
            
            if action == input.UP:
                self.scroll_index = max(0, self.scroll_index - 1)
            elif action == input.DOWN:
                self.scroll_index = min(max_scroll, self.scroll_index + 1)
            elif action == input.PAGE_UP:
                self.scroll_index = max(0, self.scroll_index - 5)
            elif action == input.PAGE_DOWN:
                self.scroll_index = min(max_scroll, self.scroll_index + 5)

    def handle_event(self, event):
        action = input.map_event(event)
        if not action: return None
        
        if self.state == 0: # Selection
            if action == input.L_BUMPER:
                return "SWITCH_TO_SETTINGS"
            elif action == input.R_BUMPER:
                return "SWITCH_TO_STATS"
            elif action in [input.UP, input.DOWN, input.PAGE_UP, input.PAGE_DOWN]:
                self._navigate(action)
            elif action == input.ACCEPT:
                if self.favorites:
                    self.target_game = self.favorites[self.selected_game_idx]
                    self.start_matching()
            elif action == input.CANCEL:
                return "SWITCH_TO_WELCOME"
            elif action == input.START:
                if self.favorites:
                    self.start_global_sync()
            elif action == input.SELECT:
                pass
                
        elif self.state == 3: # Achievement Viewer
            if action in [input.UP, input.DOWN, input.PAGE_UP, input.PAGE_DOWN]:
                self._navigate(action)
            elif action == input.CANCEL:
                self.state = 0
                self.scroll_index = 0
                
        elif self.state == 4: # Global Sync
            if action == input.CANCEL:
                self.sync_cancel = True
                self.state = 0
                self.error_msg = "Sync cancelled."
        
        return None

    def _draw_progress_bar(self, x, y, w, h, pct, color):
        self.renderer.fill((x, y, w, h), sdl2.ext.Color(50, 50, 50))
        self.renderer.fill((x, y, int(w * pct), h), sdl2.ext.Color(*color))

    def _draw_download_progress(self):
        draw_panel(self.renderer, 120, 160, 400, 140, bg_color=(20, 20, 30, 255), border_color=(0, 200, 255))
        
        pct = self.download_progress / self.total_downloads if self.total_downloads > 0 else 0
        
        render_text_shadow(self.renderer, self.font, "Syncing Badges from RA", 320, 180, (0, 200, 255), shadow_offset=2, center=True)
        render_text_shadow(self.renderer, self.font, f"Downloading: {self.download_progress} / {self.total_downloads} Files", 320, 220, (200, 200, 200), shadow_offset=1, center=True)
        
        self._draw_progress_bar(150, 250, 340, 15, pct, (0, 200, 255))
        render_text_shadow(self.renderer, self.font, f"{int(pct*100)}%", 320, 275, (100, 255, 100), shadow_offset=1, center=True)

    def draw(self):
        # Global Background
        self.renderer.fill((0, 0, 640, 480), sdl2.ext.Color(15, 15, 20))

        if self.state == 0: # Selection
            draw_panel(self.renderer, 20, 10, 600, 50, bg_color=(30, 25, 40, 255), border_color=(255, 215, 0))
            render_text_shadow(self.renderer, self.font, "Favorite Games Progress", 320, 25, (255, 215, 0), shadow_offset=2, center=True)
            
            draw_panel(self.renderer, 20, 70, 600, 360, bg_color=(20, 20, 30, 230), border_color=(80, 80, 100))
            
            if self.error_msg:
                render_text_shadow(self.renderer, self.font, self.error_msg, 320, 240, (255, 100, 100), center=True)
            elif not self.favorites:
                render_text_shadow(self.renderer, self.font, "No favorite games found.", 320, 240, (200, 200, 200), center=True)
            else:
                # Draw list
                y_start = 80
                visible_count = 8
                start_off = max(0, self.selected_game_idx - visible_count // 2)
                
                for i in range(start_off, min(len(self.favorites), start_off + visible_count)):
                    game = self.favorites[i]
                    y = y_start + (i - start_off) * 44
                    
                    is_selected = (i == self.selected_game_idx)
                    if is_selected:
                        draw_selector(self.renderer, 30, y-2, 580, 40, color=(0, 200, 255))
                        color = (255, 255, 255)
                    else:
                        color = (180, 180, 180)
                        
                    icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'game_icons', f"{game['display_name']}.png")
                    if os.path.exists(icon_path):
                        draw_image(self.renderer, icon_path, 40, y, 36, 36)
                        text_x = 85
                    else:
                        text_x = 40
                        
                    render_text_shadow(self.renderer, self.font, game["display_name"], text_x, y + 8, color, shadow_offset=1)
                    render_text_shadow(self.renderer, self.font, f"[{game.get('game_system_name', '??')}]", 500, y + 8, (120, 120, 120))

            render_text_shadow(self.renderer, self.font, "D-Pad: Select | A: View | Start: Sync All Badges | L1/R1: Tab", 320, 445, (150, 150, 150), shadow_offset=1, center=True)

        elif self.state == 1: # Loading
            draw_panel(self.renderer, 120, 180, 400, 120, bg_color=(20, 20, 30, 255), border_color=(255, 215, 0))
            render_text_shadow(self.renderer, self.font, "Establishing Link...", 320, 210, (200, 200, 100), center=True)
            render_text_shadow(self.renderer, self.font, self.loading_msg, 320, 250, (255, 255, 255), center=True)

        elif self.state == 2: # Downloading
            if self.total_downloads > 10:
                self._draw_download_progress()
            else:
                draw_panel(self.renderer, 120, 180, 400, 120, bg_color=(20, 20, 30, 255), border_color=(0, 200, 255))
                render_text_shadow(self.renderer, self.font, f"Caching Images... ({self.download_progress}/{self.total_downloads})", 320, 240, (200, 200, 100), center=True)

        elif self.state == 3: # Viewer
            # Top Stats Section
            draw_panel(self.renderer, 10, 10, 620, 80, bg_color=(30, 25, 40, 255), border_color=(255, 215, 0))
            render_text_shadow(self.renderer, self.font, self.game_data.get("Title", "Achievements"), 320, 20, (255, 215, 0), shadow_offset=2, center=True)
            
            unlocked = int(self.game_data.get("NumAwardedToUser", 0))
            total = int(self.game_data.get("NumAchievements", 0))
            pct = unlocked / total if total > 0 else 0
            
            render_text_shadow(self.renderer, self.font, f"Completion: {unlocked}/{total} ({int(pct*100)}%)", 320, 45, (255, 255, 255), center=True)
            self._draw_progress_bar(120, 70, 400, 10, pct, (0, 200, 255))
            
            # List achievements (show exactly 5)
            draw_panel(self.renderer, 10, 100, 620, 335, bg_color=(20, 20, 30, 230), border_color=(80, 80, 100))
            
            for i in range(5):
                idx = self.scroll_index + i
                if idx >= len(self.achievements): break
                
                ach = self.achievements[idx]
                y = 110 + (i * 64)
                
                is_unlocked = "DateEarned" in ach or "DateEarnedHardcore" in ach
                badge_name = ach.get("BadgeName")
                suffix = "" if is_unlocked else "_lock"
                local_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'badges', f"{badge_name}{suffix}.png")
                
                # Draw Icon Frame
                self.renderer.draw_rect((18, y-2, 68, 68), sdl2.ext.Color(100, 100, 120))
                draw_image(self.renderer, local_path, 20, y, 64, 64)
                
                # Draw Text
                title_color = (255, 255, 255) if is_unlocked else (150, 150, 150)
                desc_color = (180, 180, 180) if is_unlocked else (100, 100, 100)
                
                render_text_shadow(self.renderer, self.font, ach.get("Title", "???"), 100, y + 5, title_color, shadow_offset=1)
                render_text_shadow(self.renderer, self.font, ach.get("Description", ""), 100, y + 30, desc_color)
                
                points = ach.get("Points", 0)
                render_text_shadow(self.renderer, self.font, f"{points} pts", 540, y + 15, (150, 255, 150) if is_unlocked else (100, 150, 100))

            render_text_shadow(self.renderer, self.font, "L2/R2: Page | D-Pad: Scroll | B: Back to Games", 320, 450, (150, 150, 150), shadow_offset=1, center=True)

        elif self.state == 4: # Global Sync
            draw_panel(self.renderer, 40, 120, 560, 200, bg_color=(20, 20, 30, 255), border_color=(0, 200, 255))
            render_text_shadow(self.renderer, self.font, "Global Badge Sync", 320, 140, (0, 200, 255), shadow_offset=2, center=True)
            
            render_text_shadow(self.renderer, self.font, f"Analyzing Game {self.sync_current_idx} of {self.sync_total_games}", 320, 180, (200, 200, 200), center=True)
            render_text_shadow(self.renderer, self.font, self.sync_current_game_name, 320, 210, (255, 215, 0), center=True)
            
            if self.sync_total_downloads > 0:
                pct = self.sync_download_progress / self.sync_total_downloads
                render_text_shadow(self.renderer, self.font, f"Downloading Badges: {self.sync_download_progress} / {self.sync_total_downloads}", 320, 250, (100, 255, 100), center=True)
                self._draw_progress_bar(120, 280, 400, 15, pct, (0, 200, 255))
            else:
                render_text_shadow(self.renderer, self.font, "Scanning for missing badges...", 320, 250, (180, 180, 180), center=True)
                
            render_text_shadow(self.renderer, self.font, "Press B to Cancel", 320, 450, (255, 100, 100), shadow_offset=1, center=True)

