import sdl2
import sdl2.ext
from .components import render_text_shadow, draw_panel, draw_selector
from core import input, system

class WelcomeScreen:
    # Class-level variable to remember cursor position across screen changes
    last_selected_idx = 0

    def __init__(self, renderer, font):
        self.renderer = renderer
        self.font = font
        
        self.menu_items = [
            ("Recent Achievements", "SWITCH_TO_DASHBOARD"),
            ("Favorite Games", "SWITCH_TO_GAMES"),
            ("Profile Stats", "SWITCH_TO_STATS"),
            ("Preferences", "SWITCH_TO_SETTINGS"),
            ("Credentials", "SWITCH_TO_AUTH")
        ]
        self.selected_idx = WelcomeScreen.last_selected_idx
        
        # Navigation Repeat Logic
        self.repeat_timers = {}
        self.REPEAT_DELAY = 0.4
        self.REPEAT_INTERVAL = 0.1

    def update(self, dt):
        for action in [input.UP, input.DOWN]:
            if input.is_pressed(action):
                if action not in self.repeat_timers:
                    self.repeat_timers[action] = 0.0
                else:
                    self.repeat_timers[action] += dt
                    
                    if self.repeat_timers[action] >= self.REPEAT_DELAY:
                        self._navigate(action)
                        self.repeat_timers[action] = self.REPEAT_DELAY - self.REPEAT_INTERVAL
            else:
                if action in self.repeat_timers:
                    del self.repeat_timers[action]

    def _navigate(self, action):
        count = len(self.menu_items)
        if action == input.UP:
            self.selected_idx = (self.selected_idx - 1) % count
        elif action == input.DOWN:
            self.selected_idx = (self.selected_idx + 1) % count
            
        WelcomeScreen.last_selected_idx = self.selected_idx

    def handle_event(self, event):
        action = input.map_event(event)
        if not action: return None
        
        if action in [input.UP, input.DOWN]:
            self._navigate(action)
        elif action == input.ACCEPT:
            # Return the signal associated with the selected menu item
            return self.menu_items[self.selected_idx][1]
        elif action == input.CANCEL:
            # Tell main.py to quit the app if B is pressed on the main menu
            return "QUIT_APP"
            
        return None

    def draw(self):
        # 1. Background (Dark retro theme)
        self.renderer.fill((0, 0, 640, 480), sdl2.ext.Color(15, 15, 20))
        
        # 2. Header Frame
        draw_panel(self.renderer, 40, 20, 560, 80, bg_color=(30, 25, 40, 255), border_color=(255, 215, 0))
        render_text_shadow(self.renderer, self.font, "RetroAchievements Manager", 320, 45, (255, 215, 0), shadow_offset=3, center=True)
        
        # 3. Main Menu Panel
        draw_panel(self.renderer, 120, 140, 400, 280, bg_color=(20, 20, 30, 230), border_color=(80, 80, 100))
        
        y_start = 160
        item_height = 45
        
        for i, (label, _) in enumerate(self.menu_items):
            y = y_start + (i * item_height)
            
            # Draw selector if active
            if i == self.selected_idx:
                draw_selector(self.renderer, 130, y, 380, 40, color=(0, 200, 255))
                text_color = (255, 255, 255)
            else:
                text_color = (180, 180, 180)
                
            render_text_shadow(self.renderer, self.font, label, 320, y + 10, text_color, shadow_offset=2, center=True)
            
        # 4. Footer controls
        render_text_shadow(self.renderer, self.font, "D-Pad: Navigate | A: Select | B: Exit App", 320, 440, (150, 150, 150), shadow_offset=1, center=True)
        
        # 5. OS identifier
        os_type = system.SystemManager.get_os_type()
        os_label = {
            "SPRUCE": "SpruceOS",
            "ONION": "OnionOS",
            "GENERIC": "Custom Handheld"
        }.get(os_type, "Unknown System")
        render_text_shadow(self.renderer, self.font, f"Running on {os_label}", 320, 460, (80, 80, 80), shadow_offset=1, center=True)
