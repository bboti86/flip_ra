import sdl2
import sdl2.ext
import json
import os

from .components import render_text, render_text_shadow, draw_panel, draw_selector
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
            # Push to RetroArch and PPSSPP
            username = self.config.get("ra_username", "")
            password = self.config.get("ra_password", "")
            if username and password:
                success_ra, msg_ra = retroachievements.update_retroarch_config(username, password, self.prefs)
                success_psp, msg_psp = retroachievements.update_ppsspp_config(username, password, self.prefs)

                if success_ra and success_psp:
                    self.status_message = "Success! Configs updated (RA+PSP)."
                    self.status_color = (100, 255, 100)
                elif success_ra or success_psp:
                    self.status_message = "Partial Success (Check Logs)"
                    self.status_color = (255, 200, 100)
                else:
                    self.status_message = "Error pushing configurations."
                    self.status_color = (255, 100, 100)
            else:
                self.status_message = "Saved locally. Credentials missing to push."
                self.status_color = (100, 200, 255)
        elif action == input.CANCEL:
            return "SWITCH_TO_WELCOME"

    def draw(self):
        # 1. Background
        self.renderer.fill((0, 0, 640, 480), sdl2.ext.Color(15, 15, 20))
        
        # 2. Header Frame
        draw_panel(self.renderer, 40, 10, 560, 40, bg_color=(30, 25, 40, 255), border_color=(255, 215, 0))
        render_text_shadow(self.renderer, self.font, "RetroAchievements Preferences", 320, 20, (255, 215, 0), shadow_offset=2, center=True)
        
        # 3. Main Panel
        draw_panel(self.renderer, 40, 60, 560, 335, bg_color=(20, 20, 30, 230), border_color=(80, 80, 100))
        
        base_y = 70
        spacing = 40
        
        for i, (label, key, type) in enumerate(self.settings_map):
            y = base_y + i * spacing
            is_selected = (i == self.index)
            
            if is_selected:
                draw_selector(self.renderer, 45, y - 2, 550, 38, color=(0, 200, 255))
                label_color = (255, 255, 255)
            else:
                label_color = (180, 180, 180)
                
            render_text_shadow(self.renderer, self.font, label + ":", 60, y + 8, label_color, shadow_offset=1)
            
            val = self.prefs.get(key)
            val_text = ""
            val_color = (255, 255, 255)
            
            if type == "bool":
                val_text = "ENABLED" if val else "DISABLED"
                val_color = (100, 255, 100) if val else (255, 100, 100)
            elif type == "cycle":
                val_text = self.anchor_labels.get(val, val)
                val_color = (100, 200, 255)
                
            render_text_shadow(self.renderer, self.font, val_text, 360, y + 8, val_color, shadow_offset=1)
            
        if self.status_message:
            draw_panel(self.renderer, 40, 405, 560, 35, bg_color=(20, 20, 30, 255), border_color=(100, 100, 100))
            render_text_shadow(self.renderer, self.font, self.status_message, 320, 412, self.status_color, shadow_offset=1, center=True)
            
        render_text_shadow(self.renderer, self.font, "L1/R1: Tab | D-Pad: Select | A: Toggle | Start: Save | B: Menu", 320, 450, (150, 150, 150), shadow_offset=1, center=True)
