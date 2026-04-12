import sdl2

UP = "UP"
DOWN = "DOWN"
LEFT = "LEFT"
RIGHT = "RIGHT"
ACCEPT = "ACCEPT"
CANCEL = "CANCEL"
START = "START"
SELECT = "SELECT"
L_BUMPER = "L_BUMPER"
R_BUMPER = "R_BUMPER"

_controllers = []

def init_joysticks():
    # Use GameController for reliable Miyoo / standardized mappings
    sdl2.SDL_InitSubSystem(sdl2.SDL_INIT_GAMECONTROLLER | sdl2.SDL_INIT_JOYSTICK)
    sdl2.SDL_GameControllerEventState(sdl2.SDL_ENABLE)
    for i in range(sdl2.SDL_NumJoysticks()):
        if sdl2.SDL_IsGameController(i):
            ctrl = sdl2.SDL_GameControllerOpen(i)
            if ctrl: _controllers.append(ctrl)
        else:
            sdl2.SDL_JoystickOpen(i)

def map_event(event):
    if event.type == sdl2.SDL_KEYDOWN:
        sym = event.key.keysym.sym
        if sym == sdl2.SDLK_UP: return UP
        if sym == sdl2.SDLK_DOWN: return DOWN
        if sym == sdl2.SDLK_LEFT: return LEFT
        if sym == sdl2.SDLK_RIGHT: return RIGHT
        if sym == sdl2.SDLK_SPACE: return ACCEPT
        if sym == sdl2.SDLK_ESCAPE: return CANCEL
        if sym == sdl2.SDLK_RETURN: return START
        if sym == sdl2.SDLK_BACKSPACE: return SELECT
        if sym == sdl2.SDLK_LALT: return CANCEL
        if sym == sdl2.SDLK_TAB: return SELECT
        if sym == sdl2.SDLK_LEFTBRACKET: return L_BUMPER
        if sym == sdl2.SDLK_RIGHTBRACKET: return R_BUMPER

    elif event.type == sdl2.SDL_CONTROLLERBUTTONDOWN:
        btn = event.cbutton.button
        if btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP: return UP
        if btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN: return DOWN
        if btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT: return LEFT
        if btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT: return RIGHT
        if btn == sdl2.SDL_CONTROLLER_BUTTON_B: return ACCEPT   # Physical A button
        if btn == sdl2.SDL_CONTROLLER_BUTTON_A: return CANCEL   # Physical B button
        if btn == sdl2.SDL_CONTROLLER_BUTTON_START: return START
        if btn == sdl2.SDL_CONTROLLER_BUTTON_BACK: return SELECT
        if btn == sdl2.SDL_CONTROLLER_BUTTON_LEFTSHOULDER: return L_BUMPER
        if btn == sdl2.SDL_CONTROLLER_BUTTON_RIGHTSHOULDER: return R_BUMPER
    elif event.type == sdl2.SDL_CONTROLLERAXISMOTION:
        if event.caxis.axis == sdl2.SDL_CONTROLLER_AXIS_LEFTY:
            if event.caxis.value < -16000: return UP
            if event.caxis.value > 16000: return DOWN
        elif event.caxis.axis == sdl2.SDL_CONTROLLER_AXIS_LEFTX:
            if event.caxis.value < -16000: return LEFT
            if event.caxis.value > 16000: return RIGHT
    return None
