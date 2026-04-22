import sys
import os
import time
from core.logger import setup_logger

logger = setup_logger("main")

sys.path.append(os.path.join(os.path.dirname(__file__), 'libs'))

import sdl2
import sdl2.ext
import sdl2.sdlttf
import core.input
from ui.auth_screen import AuthScreen
from ui.dashboard_screen import DashboardScreen
from ui.games_screen import GamesScreen
from ui.settings_screen import SettingsScreen
from ui.stats_screen import StatsScreen
from ui.welcome_screen import WelcomeScreen

class Logger:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "w")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()

def rotate_logs(base_path):
    # Rotate log.1 to log.2
    log1 = base_path + ".1"
    log2 = base_path + ".2"
    if os.path.exists(log1):
        if os.path.exists(log2):
            os.remove(log2)
        os.rename(log1, log2)
    
    # Rotate log to log.1
    if os.path.exists(base_path):
        os.rename(base_path, log1)

def main():
    # Setup logging with rotation
    log_path = os.path.join(os.path.dirname(__file__), 'runtime.log')
    rotate_logs(log_path)
    
    sys.stdout = Logger(log_path)
    sys.stderr = sys.stdout
    
    logger.info("--- RA Configurator Starting ---")
    
    sdl2.ext.init()
    if sdl2.sdlttf.TTF_Init() == -1:
        logger.error(f"TTF_Init Error: {sdl2.sdlttf.TTF_GetError().decode('utf-8')}")
        sys.exit(1)
        
    core.input.init_joysticks()
    
    WIDTH, HEIGHT = 640, 480
    
    try:
        window = sdl2.ext.Window("RA Configurator", size=(WIDTH, HEIGHT), flags=sdl2.SDL_WINDOW_SHOWN | sdl2.SDL_WINDOW_FULLSCREEN)
    except Exception:
        window = sdl2.ext.Window("RA Configurator", size=(WIDTH, HEIGHT), flags=sdl2.SDL_WINDOW_SHOWN)
        
    window.show()
    
    renderer = sdl2.ext.Renderer(window, flags=sdl2.SDL_RENDERER_ACCELERATED | sdl2.SDL_RENDERER_PRESENTVSYNC)
    sdl2.SDL_SetRenderDrawBlendMode(renderer.sdlrenderer, sdl2.SDL_BLENDMODE_BLEND)
    sdl2.SDL_StartTextInput()
    
    font_path = os.path.join(os.path.dirname(__file__), 'assets', 'font.ttf')
    if not os.path.exists(font_path):
        logger.warning("Missing font asset, text rendering will fail")
        sys.exit(1)

    font = sdl2.sdlttf.TTF_OpenFont(font_path.encode('utf-8'), 20)
    
    # Initialize current_screen and timing
    current_screen = WelcomeScreen(renderer, font)
    last_time = sdl2.SDL_GetTicks()
    
    running = True
    while running:
        # Timing
        now = sdl2.SDL_GetTicks()
        dt = (now - last_time) / 1000.0  # seconds
        last_time = now

        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False
            else:
                result = current_screen.handle_event(event)
                
                if result == "QUIT_APP":
                    logger.info("Quitting Application")
                    running = False
                elif result == "SWITCH_TO_WELCOME":
                    logger.info("Switching to Welcome")
                    current_screen = WelcomeScreen(renderer, font)
                elif result == "SWITCH_TO_DASHBOARD":
                    logger.info("Switching to Dashboard")
                    current_screen = DashboardScreen(renderer, font)
                elif result == "SWITCH_TO_SETTINGS":
                    logger.info("Switching to Settings")
                    current_screen = SettingsScreen(renderer, font)
                elif result == "SWITCH_TO_GAMES":
                    logger.info("Switching to Games")
                    current_screen = GamesScreen(renderer, font)
                elif result == "SWITCH_TO_STATS":
                    logger.info("Switching to Stats")
                    current_screen = StatsScreen(renderer, font)
                elif result == "SWITCH_TO_AUTH":
                    logger.info("Switching to Auth")
                    current_screen = AuthScreen(renderer, font)

        # Update and Draw
        if hasattr(current_screen, 'update'):
            current_screen.update(dt)

        renderer.clear(sdl2.ext.Color(20, 20, 20))
        current_screen.draw()
        renderer.present()

    sdl2.SDL_StopTextInput()
    sdl2.sdlttf.TTF_CloseFont(font)
    sdl2.sdlttf.TTF_Quit()
    sdl2.ext.quit()
    sys.exit()

if __name__ == "__main__":
    main()
