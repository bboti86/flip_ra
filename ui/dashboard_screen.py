import sdl2
import sdl2.ext
import threading
from .components import render_text, render_text_shadow, draw_panel, draw_selector, draw_image
# from core import hltb
from core import input, retroachievements

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
        # self.backlog_hours = 0
        
        # Load favorites for backlog stats
        self.favorites_path = "/mnt/SDCARD/Saves/pyui-favorites.json"
        if not os.path.exists(self.favorites_path):
            self.favorites_path = "pyui-favorites.json"
        self.load_favorites()

        self.fetch_data()
        
        # Navigation Repeat Logic
        self.repeat_timers = {}
        self.REPEAT_DELAY = 0.4
        self.REPEAT_INTERVAL = 0.04 # Faster for smooth scroll
        self.PAGE_REPEAT_INTERVAL = 0.1
        self.SCROLL_STEP = 20
        self.PAGE_STEP = 180

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
                    # Start background download of badges
                    def _download_badges():
                        for ach in self.achievements:
                            bname = ach.get("BadgeName")
                            if bname:
                                retroachievements.download_badge(bname)
                    threading.Thread(target=_download_badges, daemon=True).start()
            except Exception as e:
                self.error_msg = f"Failed: {str(e)}"
            
            self.is_loading = False
            
        threading.Thread(target=_task, daemon=True).start()

    def update(self, dt):
        if self.is_loading or self.error_msg:
            return

        for action in [input.UP, input.DOWN, input.PAGE_UP, input.PAGE_DOWN]:
            if input.is_pressed(action):
                if action not in self.repeat_timers:
                    self.repeat_timers[action] = 0.0
                else:
                    self.repeat_timers[action] += dt
                    
                    delay = self.REPEAT_DELAY
                    interval = self.PAGE_REPEAT_INTERVAL if "PAGE" in action else self.REPEAT_INTERVAL
                    
                    if self.repeat_timers[action] >= delay:
                        self._navigate(action)
                        self.repeat_timers[action] = delay - interval
            else:
                if action in self.repeat_timers:
                    del self.repeat_timers[action]

    def _navigate(self, action):
        if not self.achievements: return
        
        # Calculate max scroll
        item_height = 60
        total_height = len(self.achievements) * item_height
        view_height = 340 # roughly 440 - 100
        max_scroll = max(0, total_height - view_height + 20)

        if action == input.UP:
            if self.scroll_y <= 0: # Wrap around
                self.scroll_y = max_scroll
            else:
                self.scroll_y = max(0, self.scroll_y - self.SCROLL_STEP)
        elif action == input.DOWN:
            if self.scroll_y >= max_scroll: # Wrap around
                self.scroll_y = 0
            else:
                self.scroll_y = min(max_scroll, self.scroll_y + self.SCROLL_STEP)
        elif action == input.PAGE_UP:
            self.scroll_y = max(0, self.scroll_y - self.PAGE_STEP)
        elif action == input.PAGE_DOWN:
            self.scroll_y = min(max_scroll, self.scroll_y + self.PAGE_STEP)

    def handle_event(self, event):
        action = input.map_event(event)
        if not action: return None

        if action == input.L_BUMPER:
            return "SWITCH_TO_SETTINGS"
        elif action == input.R_BUMPER:
            return "SWITCH_TO_GAMES"
        elif action in [input.UP, input.DOWN, input.PAGE_UP, input.PAGE_DOWN]:
            self._navigate(action)
        elif action == input.CANCEL:
            return "SWITCH_TO_WELCOME"
        return None

    def draw(self):
        # 1. Background
        self.renderer.fill((0, 0, 640, 480), sdl2.ext.Color(15, 15, 20))
        
        # 2. Header Frame
        draw_panel(self.renderer, 20, 10, 600, 70, bg_color=(30, 25, 40, 255), border_color=(255, 215, 0))
        render_text_shadow(self.renderer, self.font, f"Member: {self.username}", 320, 20, (200, 255, 200), shadow_offset=2, center=True)
        render_text_shadow(self.renderer, self.font, "Achievements from the last week", 320, 50, (255, 255, 255), shadow_offset=1, center=True)
        
        # 3. Main List Panel
        draw_panel(self.renderer, 20, 90, 600, 340, bg_color=(20, 20, 30, 230), border_color=(80, 80, 100))

        if self.is_loading:
            render_text_shadow(self.renderer, self.font, "Fetching Insights...", 320, 240, (200, 200, 100), center=True)
        elif self.error_msg:
            render_text_shadow(self.renderer, self.font, self.error_msg, 320, 240, (255, 100, 100), center=True)
        else:
            # Enable clipping for the list panel so items scroll smoothly underneath the borders
            clip_rect = sdl2.SDL_Rect(22, 92, 596, 336)
            sdl2.SDL_RenderSetClipRect(self.renderer.sdlrenderer, clip_rect)

            # List achievements
            y_start = 100 - self.scroll_y
            for i, ach in enumerate(self.achievements):
                curr_y = y_start + (i * 60)
                # We can now allow a wider Y range, hardware clipping handles the exact pixel cutoff
                if curr_y < 30 or curr_y > 440:
                    continue
                    
                title = ach.get("Title", "Unknown")
                game = ach.get("GameTitle", "Unknown")
                date = ach.get("Date", "").split(" ")[0]
                badge_name = ach.get("BadgeName")
                
                # Draw Icon if exists locally
                if badge_name:
                    local_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'badges', f"{badge_name}.png")
                    self.renderer.draw_rect((28, curr_y-2, 48, 48), sdl2.ext.Color(80, 80, 100))
                    draw_image(self.renderer, local_path, 30, curr_y, 44, 44)
                
                # Title in yellow
                render_text_shadow(self.renderer, self.font, f"{i+1}. {title}", 85, curr_y, (255, 215, 0), shadow_offset=1)
                # Game in grey
                render_text_shadow(self.renderer, self.font, f"{game} ({date})", 85, curr_y + 22, (180, 180, 180))

            # Disable clipping
            sdl2.SDL_RenderSetClipRect(self.renderer.sdlrenderer, None)

        # Footer
        render_text_shadow(self.renderer, self.font, "L1/R1: Tab | D-Pad: Scroll | L2/R2: Page | B: Menu", 320, 445, (150, 150, 150), shadow_offset=1, center=True)
