import sdl2
import sdl2.ext
import json
import os

from .components import render_text
from core import input, retroachievements

class SettingsScreen:
    def __init__(self, renderer, font):
        self.renderer = renderer
        self.font = font
        self.config_path = os.path.join(os.path.dirname(__file__), '..', 'settings.json')
        self.load_config()
        
        # Define the settings we manage
        self.settings_map = [
            ("Hardcore Mode", "cheevos_hardcore_mode_enable", "bool"),
            ("Achievement Anchor", "cheevos_appearance_anchor", "cycle"),
            ("Progress Tracker", "cheevos_visibility_progress_tracker", "bool"),
            ("Challenge Indicators", "cheevos_challenge_indicators", "bool"),
            ("Unlock Sound", "cheevos_unlock_sound_enable", "bool"),
            ("Auto Screenshot", "cheevos_auto_screenshot", "bool"),
            ("Lboard Start Msg", "cheevos_visibility_lboard_start", "bool"),
            ("Login Message", "cheevos_visibility_account", "bool"),
        ]
        
        self.anchor_labels = {
            "0": "Top-Left",
            "1": "Top-Right",
            "2": "Bottom-Left",
            "3": "Bottom-Right"
        }
        
        self.index = 0
        self.status_message = ""
        self.status_color = (200, 200, 200)

    def load_config(self):
        # Default Preferences
        self.prefs = {
            "cheevos_hardcore_mode_enable": False,
            "cheevos_appearance_anchor": "3",
            "cheevos_visibility_progress_tracker": True,
            "cheevos_challenge_indicators": True,
            "cheevos_unlock_sound_enable": True,
            "cheevos_auto_screenshot": True,
            "cheevos_visibility_lboard_start": False,
            "cheevos_visibility_account": False
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    full_config = json.load(f)
                    self.config = full_config
                    if "ra_prefs" in full_config:
                        self.prefs.update(full_config["ra_prefs"])
            else:
                self.config = {}
        except:
            self.config = {}

    def save_config(self):
        self.config["ra_prefs"] = self.prefs
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)

    def handle_event(self, event):
        action = input.map_event(event)
        
        if action == input.L_BUMPER:
            return "SWITCH_TO_AUTH"
        elif action == input.R_BUMPER:
            return "SWITCH_TO_DASHBOARD"
            
        if action == input.UP:
            self.index = max(0, self.index - 1)
        elif action == input.DOWN:
            self.index = min(len(self.settings_map) - 1, self.index + 1)
        elif action == input.ACCEPT:
            label, key, type = self.settings_map[self.index]
            if type == "bool":
                self.prefs[key] = not self.prefs[key]
            elif type == "cycle":
                cur = int(self.prefs[key])
                self.prefs[key] = str((cur + 1) % 4)
        elif action == input.START:
            self.save_config()
            # Push to RetroArch
            username = self.config.get("ra_username", "")
            password = self.config.get("ra_password", "")
            if username and password:
                success, msg = retroachievements.update_retroarch_config(username, password, self.prefs)
                if success:
                    self.status_message = "Success! Prefs saved & pushed to RA."
                    self.status_color = (100, 255, 100)
                else:
                    self.status_message = f"Error pushing: {msg}"
                    self.status_color = (255, 100, 100)
            else:
                self.status_message = "Saved locally. Credentials missing to push."
                self.status_color = (100, 200, 255)
        elif action == input.CANCEL:
            sdl2.SDL_EventState(sdl2.SDL_QUIT, sdl2.SDL_ENABLE)
            ev = sdl2.SDL_Event(); ev.type = sdl2.SDL_QUIT
            sdl2.SDL_PushEvent(ev)

    def draw(self):
        render_text(self.renderer, self.font, "RetroAchievements Preferences", 320, 20, (255, 255, 255), center=True)
        
        base_y = 70
        spacing = 40
        
        for i, (label, key, type) in enumerate(self.settings_map):
            color = (255, 255, 100) if i == self.index else (200, 200, 200)
            render_text(self.renderer, self.font, label + ":", 100, base_y + i * spacing, color)
            
            val = self.prefs.get(key)
            val_text = ""
            val_color = (255, 255, 255)
            
            if type == "bool":
                val_text = "ENABLED" if val else "DISABLED"
                val_color = (100, 255, 100) if val else (255, 100, 100)
            elif type == "cycle":
                val_text = self.anchor_labels.get(val, val)
                val_color = (100, 200, 255)
                
            render_text(self.renderer, self.font, val_text, 400, base_y + i * spacing, val_color)
            
        if self.status_message:
            render_text(self.renderer, self.font, self.status_message, 320, 420, self.status_color, center=True)
            
        render_text(self.renderer, self.font, "L1/R1: Tab | D-Pad: Select | A: Toggle | Start: Save", 320, 450, (150, 150, 150), center=True)
