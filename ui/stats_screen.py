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
        self.completed_games = []
        self.top_consoles = []
        self.backlog_games = []
        self.mastered_games = []
        self.completionist_pct = 0
        self.completionist_rank = "Novice Hunter"
        self.is_loading = True
        self.error_msg = None
        self.scroll_y = 0
        self.max_scroll_y = 0
        self.SCROLL_STEP = 30
        
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
                self.completed_games = retroachievements.get_user_completed_games(self.username, self.api_key)
                
                # Aggregate top systems
                consoles = {}
                for g in self.completed_games:
                    cname = g.get("ConsoleName", "Unknown")
                    if cname not in consoles:
                        consoles[cname] = {"games": 0, "achievements": 0}
                    consoles[cname]["games"] += 1
                    consoles[cname]["achievements"] += int(g.get("NumAwarded", 0))
                
                # Sort consoles by games played
                self.top_consoles = sorted(consoles.items(), key=lambda x: x[1]["games"], reverse=True)[:5]
                
                # Identify Backlog (90% to 99% completion)
                backlog = []
                for g in self.completed_games:
                    pct = float(g.get("PctWon", 0))
                    if 0.1 <= pct < 1.0:
                        backlog.append(g)
                # Sort backlog by highest completion first
                self.backlog_games = sorted(backlog, key=lambda x: float(x.get("PctWon", 0)), reverse=True)[:5]
                
                # Identify Mastered Games (100% completion)
                self.mastered_games = [g for g in self.completed_games if float(g.get("PctWon", 0)) >= 1.0]
                
                # Calculate Completionist Rank
                total_games = len(self.completed_games)
                if total_games > 0:
                    self.completionist_pct = (len(self.mastered_games) / total_games) * 100
                    if self.completionist_pct >= 75: self.completionist_rank = "Retro God"
                    elif self.completionist_pct >= 50: self.completionist_rank = "Master Hunter"
                    elif self.completionist_pct >= 25: self.completionist_rank = "Elite Collector"
                    elif self.completionist_pct >= 10: self.completionist_rank = "Veteran Hunter"
                    elif self.completionist_pct >= 5: self.completionist_rank = "Rising Star"
                    else: self.completionist_rank = "Novice Hunter"
                
                # Start background download of badges and icons
                def _background_assets():
                    # 1. Crown Jewel
                    rarest = self.stats.get("HighestRatioAch")
                    if rarest:
                        bname = rarest.get("BadgeName")
                        if bname:
                            retroachievements.download_badge(bname)
                    
                    # 2. Mastery Wall Icons
                    for g in self.mastered_games:
                        icon_url = g.get("ImageIcon")
                        game_id = g.get("GameID")
                        if icon_url and game_id:
                            retroachievements.download_game_icon(icon_url, f"game_{game_id}")
                
                threading.Thread(target=_background_assets, daemon=True).start()
                
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
        elif action == input.UP:
            self.scroll_y = max(0, self.scroll_y - self.SCROLL_STEP)
        elif action == input.DOWN:
            self.scroll_y = min(self.max_scroll_y, self.scroll_y + self.SCROLL_STEP)
        elif action == input.PAGE_UP:
            self.scroll_y = max(0, self.scroll_y - 300)
        elif action == input.PAGE_DOWN:
            self.scroll_y = min(self.max_scroll_y, self.scroll_y + 300)
        elif action == input.CANCEL:
            return "SWITCH_TO_WELCOME"
        return None

    def update(self, dt):
        if self.is_loading or self.error_msg:
            return
            
        if input.is_pressed(input.UP):
            self.scroll_y = max(0, self.scroll_y - int(400 * dt))
        elif input.is_pressed(input.DOWN):
            self.scroll_y = min(self.max_scroll_y, self.scroll_y + int(400 * dt))

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

        # Set Hardware Clipping for Main Panel to allow scrolling
        clip_rect = sdl2.SDL_Rect(42, 62, 556, 366)
        sdl2.SDL_RenderSetClipRect(self.renderer.sdlrenderer, clip_rect)

        # 1. Progression Gauge
        y_offset = 80 - self.scroll_y
        
        rank = self.stats.get("Rank", "Unknown")
        true_pts = self.stats.get("TotalTruePoints", 0)
        milestone_step = 5000 if true_pts > 10000 else 1000
        next_milestone = math.ceil((true_pts + 1) / milestone_step) * milestone_step
        progression_pct = true_pts / next_milestone if next_milestone > 0 else 0
        
        render_text_shadow(self.renderer, self.font, f"Global Rank: #{rank}", 80, y_offset, (200, 200, 255), shadow_offset=1)
        render_text_shadow(self.renderer, self.font, f"True Points: {true_pts} / {next_milestone}", 80, y_offset + 30, (200, 200, 200), shadow_offset=1)
        self._draw_bar(80, y_offset + 60, 480, 25, progression_pct, (0, 200, 255), (30, 30, 50))
        self.renderer.draw_rect((79, y_offset + 59, 482, 27), sdl2.ext.Color(80, 80, 100)) # Bar border

        # 2. Purity Meter (Hardcore vs Softcore)
        y_offset += 110
        hc_pts = self.stats.get("HCPoints", 0)
        sc_pts = self.stats.get("SCPoints", 0)
        total_base = hc_pts + sc_pts
        purity_pct = hc_pts / total_base if total_base > 0 else (1.0 if hc_pts > 0 else 0)
        
        render_text_shadow(self.renderer, self.font, "Hardcore Purity:", 80, y_offset, (255, 215, 0), shadow_offset=1)
        
        # Completionist Rank (Right Aligned)
        rank_color = (255, 255, 100) if self.completionist_pct > 25 else (200, 200, 200)
        render_text_shadow(self.renderer, self.font, f"Rank: {self.completionist_rank}", 560, y_offset, rank_color, shadow_offset=1, right=True)
        
        render_text_shadow(self.renderer, self.font, f"{int(purity_pct * 100)}% ({hc_pts} HC / {sc_pts} SC)", 80, y_offset + 30, (200, 200, 200), shadow_offset=1)
        self._draw_bar(80, y_offset + 60, 480, 25, purity_pct, (255, 215, 0), (140, 140, 140))
        self.renderer.draw_rect((79, y_offset + 59, 482, 27), sdl2.ext.Color(80, 80, 100)) # Bar border
        
        # Mastery Percentage inside Purity bar area (centered)
        render_text(self.renderer, self.font, f"{int(self.completionist_pct)}% Mastery Rate", 320, y_offset + 60, (0, 0, 0), center=True)
        
        # 2.5 Mastery Wall (Badges for 100% games)
        y_offset += 110
        render_text_shadow(self.renderer, self.font, "Mastery Wall (100%):", 80, y_offset, (255, 215, 0), shadow_offset=1)
        y_offset += 35
        
        if self.mastered_games:
            grid_x = 80
            grid_y = y_offset
            icons_per_row = 6
            icon_size = 64
            spacing = 10
            
            for i, g in enumerate(self.mastered_games):
                game_id = g.get("GameID")
                local_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'game_icons', f"game_{game_id}.png")
                
                # Draw icon frame
                frame_rect = (grid_x + (i % icons_per_row) * (icon_size + spacing), 
                            grid_y + (i // icons_per_row) * (icon_size + spacing), 
                            icon_size, icon_size)
                self.renderer.draw_rect(frame_rect, sdl2.ext.Color(80, 80, 100))
                
                if os.path.exists(local_path):
                    draw_image(self.renderer, local_path, frame_rect[0] + 2, frame_rect[1] + 2, icon_size - 4, icon_size - 4)
                
                # Move y_offset down based on how many rows we drew
                if i == len(self.mastered_games) - 1:
                    rows = (i // icons_per_row) + 1
                    y_offset += rows * (icon_size + spacing)
        else:
            render_text_shadow(self.renderer, self.font, "No games mastered yet.", 80, y_offset, (150, 150, 150), shadow_offset=1)
            y_offset += 30

        # 3. The Crown Jewel
        y_offset += 20
        rarest = self.stats.get("HighestRatioAch")
        render_text_shadow(self.renderer, self.font, "Recent Crown Jewel:", 80, y_offset, (255, 50, 150), shadow_offset=1)
        if rarest:
            title = rarest.get("Title", "Unknown")
            game = rarest.get("GameTitle", "Unknown")
            ratio = rarest.get("HardcoreRetroRatio", rarest.get("RetroRatio", 0))
            badge_name = rarest.get("BadgeName")
            
            draw_selector(self.renderer, 75, y_offset + 35, 490, 70, color=(255, 50, 150))
            
            text_x = 85
            if badge_name:
                local_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'badges', f"{badge_name}.png")
                self.renderer.draw_rect((83, y_offset + 38, 64, 64), sdl2.ext.Color(80, 80, 100))
                draw_image(self.renderer, local_path, 85, y_offset + 40, 60, 60)
                text_x = 155
            
            render_text_shadow(self.renderer, self.font, f"{title} (Ratio: {ratio})", text_x, y_offset + 45, (255, 255, 100), shadow_offset=1)
            render_text_shadow(self.renderer, self.font, f"in {game}", text_x, y_offset + 75, (180, 180, 180), shadow_offset=1)
        else:
            render_text_shadow(self.renderer, self.font, "No recent achievements found.", 80, y_offset + 40, (150, 150, 150), shadow_offset=1)

        # 4. Console Dominance
        y_offset += 130
        render_text_shadow(self.renderer, self.font, "Console Dominance (Top 5):", 80, y_offset, (100, 255, 100), shadow_offset=1)
        y_offset += 35
        
        if self.top_consoles:
            max_games = max((c[1]["games"] for c in self.top_consoles)) if self.top_consoles else 1
            max_achs = max((c[1]["achievements"] for c in self.top_consoles)) if self.top_consoles else 1
            
            for cname, data in self.top_consoles:
                g_count = data["games"]
                a_count = data["achievements"]
                render_text_shadow(self.renderer, self.font, cname, 80, y_offset, (255, 255, 255), shadow_offset=1)
                y_offset += 25
                
                # Games Played Bar
                self._draw_bar(80, y_offset, 480, 24, g_count / max_games if max_games else 0, (100, 255, 100), (30, 50, 30))
                render_text(self.renderer, self.font, f"{g_count} Games", 85, y_offset, (0, 0, 0)) # Text inside bar
                y_offset += 30
                
                # Achievements Earned Bar
                self._draw_bar(80, y_offset, 480, 24, a_count / max_achs if max_achs else 0, (255, 215, 0), (50, 50, 30))
                render_text(self.renderer, self.font, f"{a_count} Achievements", 85, y_offset, (0, 0, 0))
                y_offset += 35
        # 5. Backlog Tracker (Closest to Mastery)
        y_offset += 15
        render_text_shadow(self.renderer, self.font, "Backlog Tracker (10%+): Top 5", 80, y_offset, (255, 150, 50), shadow_offset=1)
        y_offset += 35
        
        if self.backlog_games:
            for g in self.backlog_games:
                title = g.get("Title", "Unknown")
                pct = float(g.get("PctWon", 0)) * 100
                console = g.get("ConsoleName", "Unknown")
                
                render_text_shadow(self.renderer, self.font, f"{title} ({console})", 80, y_offset, (255, 255, 255), shadow_offset=1)
                y_offset += 25
                self._draw_bar(80, y_offset, 480, 18, pct/100, (255, 150, 50), (60, 40, 20))
                render_text(self.renderer, self.font, f"{int(pct)}% Complete", 85, y_offset - 2, (0, 0, 0))
                y_offset += 30
        else:
            render_text_shadow(self.renderer, self.font, "No games near mastery.", 80, y_offset, (150, 150, 150), shadow_offset=1)
            y_offset += 30

        # Calculate dynamic scroll limit based on final rendered content height
        total_content_height = (y_offset + self.scroll_y) - 80
        self.max_scroll_y = max(0, total_content_height - 366 + 40) # 366 is clip height, 40 is padding

        # Disable Clipping
        sdl2.SDL_RenderSetClipRect(self.renderer.sdlrenderer, None)

        render_text_shadow(self.renderer, self.font, "L1/R1: Tab | D-Pad: Scroll | L2/R2: Page | B: Menu", 320, 450, (150, 150, 150), shadow_offset=1, center=True)
