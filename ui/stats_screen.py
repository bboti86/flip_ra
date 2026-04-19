import sdl2
import sdl2.ext
import threading
import json
import os
import math

from .components import render_text, render_text_shadow, draw_panel, draw_selector, draw_image
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
                
                # Start background download of the Crown Jewel badge
                def _download_rarest_badge():
                    rarest = self.stats.get("HighestRatioAch")
                    if rarest:
                        bname = rarest.get("BadgeName")
                        if bname:
                            retroachievements.download_badge(bname)
                threading.Thread(target=_download_rarest_badge, daemon=True).start()
                
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
            return "SWITCH_TO_WELCOME"
        return None

    def _draw_bar(self, x, y, w, h, fill_pct, fill_color, bg_color):
        fill_pct = max(0.0, min(1.0, fill_pct))
        self.renderer.fill((x, y, w, h), sdl2.ext.Color(*bg_color))
        self.renderer.fill((x, y, int(w * fill_pct), h), sdl2.ext.Color(*fill_color))

    def draw(self):
        # 1. Background
        self.renderer.fill((0, 0, 640, 480), sdl2.ext.Color(15, 15, 20))
        
        # 2. Header Frame
        draw_panel(self.renderer, 40, 10, 560, 40, bg_color=(30, 25, 40, 255), border_color=(255, 215, 0))
        render_text_shadow(self.renderer, self.font, "Profile Stats & Progression", 320, 20, (255, 215, 0), shadow_offset=2, center=True)
        
        # 3. Main Panel
        draw_panel(self.renderer, 40, 60, 560, 370, bg_color=(20, 20, 30, 230), border_color=(80, 80, 100))
        
        if self.is_loading:
            render_text_shadow(self.renderer, self.font, "Calculating metrics...", 320, 220, (200, 200, 100), center=True)
            return

        if self.error_msg:
            render_text_shadow(self.renderer, self.font, self.error_msg, 320, 220, (255, 100, 100), center=True)
            return

        # 1. Progression Gauge
        rank = self.stats.get("Rank", "Unknown")
        true_pts = self.stats.get("TotalTruePoints", 0)
        
        # Calculate dynamic next milestone for True Points (leaderboard metric)
        milestone_step = 5000 if true_pts > 10000 else 1000
        next_milestone = math.ceil((true_pts + 1) / milestone_step) * milestone_step
        
        progression_pct = true_pts / next_milestone if next_milestone > 0 else 0
        
        render_text_shadow(self.renderer, self.font, f"Global Rank: #{rank}", 80, 80, (200, 200, 255), shadow_offset=1)
        render_text_shadow(self.renderer, self.font, f"True Points: {true_pts} / {next_milestone}", 80, 110, (200, 200, 200), shadow_offset=1)
        self._draw_bar(80, 140, 480, 25, progression_pct, (0, 200, 255), (30, 30, 50))
        self.renderer.draw_rect((79, 139, 482, 27), sdl2.ext.Color(80, 80, 100)) # Bar border

        # 2. Purity Meter (Hardcore vs Softcore)
        hc_pts = self.stats.get("HCPoints", 0)
        sc_pts = self.stats.get("SCPoints", 0)
        total_base = hc_pts + sc_pts
        
        purity_pct = hc_pts / total_base if total_base > 0 else (1.0 if hc_pts > 0 else 0)
        
        render_text_shadow(self.renderer, self.font, "Hardcore Purity:", 80, 190, (255, 215, 0), shadow_offset=1)
        render_text_shadow(self.renderer, self.font, f"{int(purity_pct * 100)}% ({hc_pts} HC / {sc_pts} SC)", 80, 220, (200, 200, 200), shadow_offset=1)
        # Draw Softcore as silver background, Hardcore as Gold fill
        self._draw_bar(80, 250, 480, 25, purity_pct, (255, 215, 0), (140, 140, 140))
        self.renderer.draw_rect((79, 249, 482, 27), sdl2.ext.Color(80, 80, 100)) # Bar border
        
        # 3. The Crown Jewel
        rarest = self.stats.get("HighestRatioAch")
        render_text_shadow(self.renderer, self.font, "Recent Crown Jewel:", 80, 300, (255, 50, 150), shadow_offset=1)
        if rarest:
            title = rarest.get("Title", "Unknown")
            game = rarest.get("GameTitle", "Unknown")
            ratio = rarest.get("HardcoreRetroRatio", rarest.get("RetroRatio", 0))
            badge_name = rarest.get("BadgeName")
            
            draw_selector(self.renderer, 75, 335, 490, 70, color=(255, 50, 150))
            
            # Draw Icon if exists locally
            text_x = 85
            if badge_name:
                local_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'badges', f"{badge_name}.png")
                self.renderer.draw_rect((83, 338, 64, 64), sdl2.ext.Color(80, 80, 100))
                draw_image(self.renderer, local_path, 85, 340, 60, 60)
                text_x = 155
            
            render_text_shadow(self.renderer, self.font, f"{title} (Ratio: {ratio})", text_x, 345, (255, 255, 100), shadow_offset=1)
            render_text_shadow(self.renderer, self.font, f"in {game}", text_x, 375, (180, 180, 180), shadow_offset=1)
        else:
            render_text_shadow(self.renderer, self.font, "No recent achievements found.", 80, 340, (150, 150, 150), shadow_offset=1)

        render_text_shadow(self.renderer, self.font, "L1/R1: Tab | B: Menu", 320, 450, (150, 150, 150), shadow_offset=1, center=True)
