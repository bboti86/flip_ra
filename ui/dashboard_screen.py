import sdl2
import sdl2.ext
import threading
from .components import render_text
from core import input, retroachievements, hltb

import os
import json

class DashboardScreen:
    def __init__(self, renderer, font):
        self.renderer = renderer
        self.font = font
        self.config_path = os.path.join(os.path.dirname(__file__), '..', 'settings.json')
        
        self.load_config()
        self.username = self.config.get("ra_username", "")
        self.api_key = self.config.get("ra_api_key", "")
        
        self.achievements = []
        self.is_loading = True
        self.error_msg = None
        self.scroll_y = 0
        self.favorites = []
        self.backlog_hours = 0
        
        # Load favorites for backlog stats
        self.favorites_path = "/mnt/SDCARD/Saves/pyui-favorites.json"
        if not os.path.exists(self.favorites_path):
            self.favorites_path = "pyui-favorites.json"
        self.load_favorites()

        self.fetch_data()

    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except:
            self.config = {"ra_username": "", "ra_api_key": ""}

    def load_favorites(self):
        try:
            if os.path.exists(self.favorites_path):
                with open(self.favorites_path, 'r') as f:
                    self.favorites = json.load(f)
        except: pass

    def fetch_data(self):
        def _task():
            # 1. Fetch RA Activity
            try:
                data = retroachievements.get_recent_achievements(self.username, self.api_key)
                if not data:
                    self.error_msg = "No achievements found or API error."
                else:
                    self.achievements = data
            except Exception as e:
                self.error_msg = f"Failed: {str(e)}"
            
            # 2. Calculate Backlog Hours (Async)
            total = 0
            for g in self.favorites:
                data = hltb.get_game_times(g["display_name"])
                if data:
                    total += data["main"]
            self.backlog_hours = total
            
            self.is_loading = False
            
        threading.Thread(target=_task, daemon=True).start()

    def handle_event(self, event):
        action = input.map_event(event)

        if action == input.L_BUMPER:
            return "SWITCH_TO_SETTINGS"
        elif action == input.R_BUMPER:
            return "SWITCH_TO_GAMES"

        if action == input.UP:
            self.scroll_y = max(0, self.scroll_y - 20)
        elif action == input.DOWN:
            self.scroll_y += 20
        elif action == input.CANCEL:
            # Signal back to go to Auth
            return "SWITCH_TO_AUTH"
        return None

    def draw(self):
        render_text(self.renderer, self.font, f"Member: {self.username}", 320, 20, (200, 255, 200), center=True)
        render_text(self.renderer, self.font, "Achievements from the last week", 320, 50, (255, 255, 255), center=True)
        
        if self.is_loading:
            render_text(self.renderer, self.font, "Fetching Insights...", 320, 200, (200, 200, 100), center=True)
            return

        # Backlog Summary
        if self.backlog_hours > 0:
            render_text(self.renderer, self.font, f"Backlog: ~{int(self.backlog_hours)}h remaining", 320, 75, (100, 200, 255), center=True)

        if self.error_msg:
            render_text(self.renderer, self.font, self.error_msg, 320, 200, (255, 100, 100), center=True)
            return

        # List achievements
        y_start = 100 - self.scroll_y
        for i, ach in enumerate(self.achievements):
            curr_y = y_start + (i * 60)
            if curr_y < 80 or curr_y > 440:
                continue
                
            title = ach.get("Title", "Unknown")
            game = ach.get("GameTitle", "Unknown")
            date = ach.get("Date", "").split(" ")[0]
            
            # Title in yellow
            render_text(self.renderer, self.font, f"{i+1}. {title}", 30, curr_y, (255, 255, 100))
            # Game in grey
            render_text(self.renderer, self.font, f"   {game} ({date})", 30, curr_y + 25, (180, 180, 180))

        render_text(self.renderer, self.font, "L1/R1: Tab | D-Pad: Scroll | B: Back", 320, 450, (150, 150, 150), center=True)
