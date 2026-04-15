import sdl2
import sdl2.ext
import threading
import json
import os
import math

from .components import render_text
from core import input, retroachievements

class StatsScreen:
    def __init__(self, renderer, font):
        self.renderer = renderer
        self.font = font
        self.config_path = os.path.join(os.path.dirname(__file__), '..', 'settings.json')
        
        self.load_config()
        self.username = self.config.get("ra_username", "")
        self.api_key = self.config.get("ra_api_key", "")
        
        self.stats = {}
        self.is_loading = True
        self.error_msg = None
        
        self.fetch_data()

    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except:
            self.config = {"ra_username": "", "ra_api_key": ""}

    def fetch_data(self):
        def _task():
            try:
                self.stats = retroachievements.get_user_stats(self.username, self.api_key)
            except Exception as e:
                self.error_msg = f"Failed to fetch stats: {e}"
            self.is_loading = False
            
        threading.Thread(target=_task, daemon=True).start()

    def handle_event(self, event):
        action = input.map_event(event)

        if action == input.L_BUMPER:
            return "SWITCH_TO_GAMES"
        elif action == input.R_BUMPER:
            return "SWITCH_TO_AUTH"

        if action == input.CANCEL:
            return "SWITCH_TO_AUTH"
        return None

    def _draw_bar(self, x, y, w, h, fill_pct, fill_color, bg_color):
        fill_pct = max(0.0, min(1.0, fill_pct))
        self.renderer.fill((x, y, w, h), sdl2.ext.Color(*bg_color))
        self.renderer.fill((x, y, int(w * fill_pct), h), sdl2.ext.Color(*fill_color))

    def draw(self):
        render_text(self.renderer, self.font, "Profile Stats & Progression", 320, 20, (255, 255, 255), center=True)
        
        if self.is_loading:
            render_text(self.renderer, self.font, "Calculating metrics...", 320, 200, (200, 200, 100), center=True)
            return

        if self.error_msg:
            render_text(self.renderer, self.font, self.error_msg, 320, 200, (255, 100, 100), center=True)
            return

        # 1. Progression Gauge
        rank = self.stats.get("Rank", "Unknown")
        total_pts = self.stats.get("TotalPoints", 0)
        
        # Calculate dynamic next milestone (e.g. next 5000)
        milestone_step = 5000 if total_pts > 10000 else 1000
        next_milestone = math.ceil((total_pts + 1) / milestone_step) * milestone_step
        
        progression_pct = total_pts / next_milestone if next_milestone > 0 else 0
        
        render_text(self.renderer, self.font, f"Global Rank: #{rank}", 100, 80, (200, 200, 255))
        render_text(self.renderer, self.font, f"Points: {total_pts} / {next_milestone} (Next Milestone)", 100, 110, (200, 200, 200))
        self._draw_bar(100, 140, 440, 25, progression_pct, (100, 200, 255), (50, 50, 80))

        # 2. Purity Meter (Hardcore vs Softcore)
        true_pts = self.stats.get("TotalTruePoints", 0)
        soft_pts = max(0, total_pts - true_pts)
        
        purity_pct = true_pts / total_pts if total_pts > 0 else 0
        
        render_text(self.renderer, self.font, "Hardcore Purity:", 100, 200, (255, 200, 100))
        render_text(self.renderer, self.font, f"{int(purity_pct * 100)}% ({true_pts} HC / {soft_pts} SC)", 100, 230, (200, 200, 200))
        # Draw Softcore as silver background, Hardcore as Gold fill
        self._draw_bar(100, 260, 440, 25, purity_pct, (255, 215, 0), (192, 192, 192))
        
        # 3. The Crown Jewel
        rarest = self.stats.get("HighestRatioAch")
        render_text(self.renderer, self.font, "Recent Crown Jewel:", 100, 320, (255, 50, 150))
        if rarest:
            title = rarest.get("Title", "Unknown")
            game = rarest.get("GameTitle", "Unknown")
            ratio = rarest.get("HardcoreRetroRatio", rarest.get("RetroRatio", 0))
            
            render_text(self.renderer, self.font, f"{title} (Ratio: {ratio})", 100, 350, (255, 255, 100))
            render_text(self.renderer, self.font, f"in {game}", 100, 380, (180, 180, 180))
        else:
            render_text(self.renderer, self.font, "No recent achievements found.", 100, 350, (150, 150, 150))

        render_text(self.renderer, self.font, "L1/R1: Tab | B: Back", 320, 450, (150, 150, 150), center=True)
