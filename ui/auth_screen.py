import sdl2
import sdl2.ext
import json
import threading
import os

from .components import TextInput, OnScreenKeyboard, render_text, render_text_shadow, draw_panel, draw_selector
from core import input, retroachievements

class AuthScreen:
    def __init__(self, renderer, font):
        self.renderer = renderer
        self.font = font
        self.config_path = os.path.join(os.path.dirname(__file__), '..', 'settings.json')
        self.load_config()

        self.input_user = TextInput(100, 100, 440, 40, self.font)
        self.input_user.text = self.config.get("ra_username", "")
        self.input_pwd = TextInput(100, 180, 440, 40, self.font, is_password=True)
        self.input_pwd.text = self.config.get("ra_password", "")
        self.input_key = TextInput(100, 260, 440, 40, self.font, is_password=True)
        self.input_key.text = self.config.get("ra_api_key", "")
        
        self.auth_inputs = [self.input_user, self.input_pwd, self.input_key]
        self.auth_index = 0
        self.osk = OnScreenKeyboard(self.font)
        
        if self.config.get("ra_username") and self.config.get("ra_api_key"):
            self.status_message = "Authenticated. START: Dashboard | SELECT: Update Config"
            self.status_color = (100, 255, 100)
        else:
            self.status_message = "D-Pad: Select | A: Type | Start: Verify | B: Exit"
            self.status_color = (150, 150, 150)
            
        self.is_verifying = False
        self.is_confirming = False

    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except:
            self.config = {"ra_username": "", "ra_api_key": ""}
            
    def save_config(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)

    def verify_and_save(self):
        self.is_verifying = True
        self.is_confirming = False
        self.status_message = "Verifying with RetroAchievements API..."
        self.status_color = (200, 200, 100)
        
        username = self.input_user.text
        password = self.input_pwd.text
        api_key = self.input_key.text
        
        # Cache aggressively
        self.config["ra_username"] = username
        self.config["ra_password"] = password
        self.config["ra_api_key"] = api_key
        self.save_config()
        
        def _task():
            success, msg = retroachievements.verify_credentials(username, api_key)
            if not success:
                print(f"[AUTH] Verification failed for user {username}: {msg}")
                self.status_message = f"Error: {msg}"
                self.status_color = (255, 100, 100)
                self.is_verifying = False
                return
            
            print(f"[AUTH] Credentials verified successfully for user {username}")
            self.status_message = "Valid! Press A to Overwrite Retroarch Config, or B to Cancel."
            self.status_color = (100, 255, 255)
            self.is_verifying = False
            self.is_confirming = True
            
        threading.Thread(target=_task, daemon=True).start()

    def do_update(self):
        self.is_confirming = False
        username = self.input_user.text
        password = self.input_pwd.text
        api_key = self.input_key.text
        prefs = self.config.get("ra_prefs", {})
        
        s_ra, m_ra = retroachievements.update_retroarch_config(username, password, prefs)
        s_psp, m_psp = retroachievements.update_ppsspp_config(username, password, prefs)
        
        if not s_ra and not s_psp:
            self.status_message = f"Error: RA({m_ra}) PSP({m_psp})"
            self.status_color = (255, 100, 100)
            return
            
        self.config["ra_username"] = username
        self.config["ra_password"] = password
        self.config["ra_api_key"] = api_key
        self.save_config()
        
        status = "Success! Configs Updated (RA+PSP)" if s_ra and s_psp else "Partial Success!"
        self.status_message = f"{status}. Press START for Dashboard."
        self.status_color = (100, 255, 100)

    def handle_event(self, event):
        action = input.map_event(event)

        if self.is_verifying:
            return  # Block input while verifying
            
        if self.is_confirming:
            if action == input.ACCEPT:
                self.do_update()
            elif action == input.CANCEL:
                self.is_confirming = False
                self.status_message = "Update Terminated."
                self.status_color = (250, 150, 50)
            return

        is_active = self.input_user.active or self.input_pwd.active or self.input_key.active
        
        active_input = None
        if self.input_user.active: active_input = self.input_user
        elif self.input_pwd.active: active_input = self.input_pwd
        elif self.input_key.active: active_input = self.input_key
        
        if not is_active:
            if action == input.L_BUMPER:
                return "SWITCH_TO_STATS"
            elif action == input.R_BUMPER:
                return "SWITCH_TO_SETTINGS"
            elif action == input.UP:
                self.auth_index = max(0, self.auth_index - 1)
            elif action == input.DOWN:
                self.auth_index = min(len(self.auth_inputs) - 1, self.auth_index + 1)
            elif action == input.ACCEPT:
                self.auth_inputs[self.auth_index].active = True
            elif action == input.START:
                # If we are already authenticated OR just succeeded, go to dashboard
                if (self.config.get("ra_username") and self.config.get("ra_api_key")) or "Success" in self.status_message:
                    return "SWITCH_TO_DASHBOARD"
                self.verify_and_save()
            elif action == input.SELECT:
                self.verify_and_save()
            elif action == input.CANCEL:
                # Return to Welcome Menu instead of quitting
                return "SWITCH_TO_WELCOME"
        else:
            osk_result = self.osk.handle_action(action)
            if osk_result == "BACK":
                active_input.text = active_input.text[:-1]
            elif osk_result in ["DONE", "DONE_CANCEL"] or action == input.START:
                active_input.active = False
            elif osk_result == "SPACE":
                active_input.text += " "
            elif osk_result:
                active_input.text += osk_result

    def draw(self):
        # 1. Background
        self.renderer.fill((0, 0, 640, 480), sdl2.ext.Color(15, 15, 20))
        
        # 2. Header Frame
        draw_panel(self.renderer, 40, 10, 560, 40, bg_color=(30, 25, 40, 255), border_color=(255, 215, 0))
        render_text_shadow(self.renderer, self.font, "RetroAchievements Authenticator", 320, 20, (255, 215, 0), shadow_offset=2, center=True)
        
        # 3. Main Form Panel
        draw_panel(self.renderer, 60, 60, 520, 240, bg_color=(20, 20, 30, 230), border_color=(80, 80, 100))
        
        c_user = (0, 200, 255) if self.auth_index == 0 else (180, 180, 180)
        render_text_shadow(self.renderer, self.font, "Username:", 80, 70, c_user, shadow_offset=1)
        self.input_user.rect.x = 80
        self.input_user.rect.y = 100
        self.input_user.rect.w = 480
        if self.auth_index == 0: draw_selector(self.renderer, 78, 98, 484, 44, color=c_user)
        self.input_user.draw(self.renderer)
        
        c_pwd = (0, 200, 255) if self.auth_index == 1 else (180, 180, 180)
        render_text_shadow(self.renderer, self.font, "Password:", 80, 150, c_pwd, shadow_offset=1)
        self.input_pwd.rect.x = 80
        self.input_pwd.rect.y = 180
        self.input_pwd.rect.w = 480
        if self.auth_index == 1: draw_selector(self.renderer, 78, 178, 484, 44, color=c_pwd)
        self.input_pwd.draw(self.renderer)

        c_key = (0, 200, 255) if self.auth_index == 2 else (180, 180, 180)
        render_text_shadow(self.renderer, self.font, "Web API Key:", 80, 230, c_key, shadow_offset=1)
        self.input_key.rect.x = 80
        self.input_key.rect.y = 260
        self.input_key.rect.w = 480
        if self.auth_index == 2: draw_selector(self.renderer, 78, 258, 484, 44, color=c_key)
        self.input_key.draw(self.renderer)

        if self.input_user.active or self.input_pwd.active or self.input_key.active:
            self.osk.draw(self.renderer)
        else:
            # Status Panel
            draw_panel(self.renderer, 40, 310, 560, 50, bg_color=(20, 20, 30, 255), border_color=(100, 100, 100))
            render_text_shadow(self.renderer, self.font, self.status_message, 320, 325, self.status_color, shadow_offset=1, center=True)
            
            # Footer
            render_text_shadow(self.renderer, self.font, "L1/R1: Tab | D-Pad: Select | A: Type | Start: Verify | B: Menu", 320, 440, (150, 150, 150), shadow_offset=1, center=True)
