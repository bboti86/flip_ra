import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'libs'))

import sdl2
import sdl2.ext
import sdl2.sdlttf
import core.input
from ui.auth_screen import AuthScreen
from ui.dashboard_screen import DashboardScreen
from ui.settings_screen import SettingsScreen
from ui.stats_screen import StatsScreen

def main():
    sdl2.ext.init()
    if sdl2.sdlttf.TTF_Init() == -1:
        print(f"TTF_Init Error: {sdl2.sdlttf.TTF_GetError().decode('utf-8')}")
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
        print("Missing font asset")
        sys.exit(1)

    font = sdl2.sdlttf.TTF_OpenFont(font_path.encode('utf-8'), 20)
    
    # Initialize current screen
    current_screen = AuthScreen(renderer, font)
    
    running = True
    while running:
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False
            else:
                result = current_screen.handle_event(event)
                
                if result == "SWITCH_TO_DASHBOARD":
                    current_screen = DashboardScreen(renderer, font)
                elif result == "SWITCH_TO_SETTINGS":
                    current_screen = SettingsScreen(renderer, font)
                elif result == "SWITCH_TO_STATS":
                    current_screen = StatsScreen(renderer, font)
                elif result == "SWITCH_TO_AUTH":
                    current_screen = AuthScreen(renderer, font)

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
