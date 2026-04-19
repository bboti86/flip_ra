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
PAGE_UP = "PAGE_UP"
PAGE_DOWN = "PAGE_DOWN"

_controllers = []
_axis_states = {}
_action_states = {}

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

def is_pressed(action):
    return _action_states.get(action, False)

def map_event(event):
    action = None
    pressed = False

    if event.type == sdl2.SDL_KEYDOWN or event.type == sdl2.SDL_KEYUP:
        pressed = (event.type == sdl2.SDL_KEYDOWN)
        sym = event.key.keysym.sym
        if sym == sdl2.SDLK_UP: action = UP
        elif sym == sdl2.SDLK_DOWN: action = DOWN
        elif sym == sdl2.SDLK_LEFT: action = LEFT
        elif sym == sdl2.SDLK_RIGHT: action = RIGHT
        elif sym == sdl2.SDLK_SPACE: action = ACCEPT
        elif sym == sdl2.SDLK_ESCAPE: action = CANCEL
        elif sym == sdl2.SDLK_RETURN: action = START
        elif sym == sdl2.SDLK_BACKSPACE: action = SELECT
        elif sym == sdl2.SDLK_LALT: action = CANCEL
        elif sym == sdl2.SDLK_TAB: action = SELECT
        elif sym == sdl2.SDLK_LEFTBRACKET: action = L_BUMPER
        elif sym == sdl2.SDLK_RIGHTBRACKET: action = R_BUMPER
        elif sym == sdl2.SDLK_PAGEUP: action = PAGE_UP
        elif sym == sdl2.SDLK_PAGEDOWN: action = PAGE_DOWN

    elif event.type == sdl2.SDL_CONTROLLERBUTTONDOWN or event.type == sdl2.SDL_CONTROLLERBUTTONUP:
        pressed = (event.type == sdl2.SDL_CONTROLLERBUTTONDOWN)
        btn = event.cbutton.button
        if btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP: action = UP
        elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN: action = DOWN
        elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT: action = LEFT
        elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT: action = RIGHT
        elif btn == sdl2.SDL_CONTROLLER_BUTTON_B: action = ACCEPT   # Physical A button
        elif btn == sdl2.SDL_CONTROLLER_BUTTON_A: action = CANCEL   # Physical B button
        elif btn == sdl2.SDL_CONTROLLER_BUTTON_START: action = START
        elif btn == sdl2.SDL_CONTROLLER_BUTTON_BACK: action = SELECT
        elif btn == sdl2.SDL_CONTROLLER_BUTTON_LEFTSHOULDER: action = L_BUMPER
        elif btn == sdl2.SDL_CONTROLLER_BUTTON_RIGHTSHOULDER: action = R_BUMPER
        
    elif event.type == sdl2.SDL_CONTROLLERAXISMOTION:
        axis = event.caxis.axis
        val = event.caxis.value
        prev_val = _axis_states.get(axis, 0)
        _axis_states[axis] = val

        # Handle D-pad like behavior for sticks and triggers
        if axis == sdl2.SDL_CONTROLLER_AXIS_LEFTY:
            if val < -16000 and prev_val >= -16000: action, pressed = UP, True
            elif val > -16000 and prev_val <= -16000: action, pressed = UP, False
            if val > 16000 and prev_val <= 16000: action, pressed = DOWN, True
            elif val < 16000 and prev_val >= 16000: action, pressed = DOWN, False
        elif axis == sdl2.SDL_CONTROLLER_AXIS_LEFTX:
            if val < -16000 and prev_val >= -16000: action, pressed = LEFT, True
            elif val > -16000 and prev_val <= -16000: action, pressed = LEFT, False
            if val > 16000 and prev_val <= 16000: action, pressed = RIGHT, True
            elif val < 16000 and prev_val >= 16000: action, pressed = RIGHT, False
        elif axis == sdl2.SDL_CONTROLLER_AXIS_TRIGGERLEFT:
            if val > 16000 and prev_val <= 16000: action, pressed = PAGE_UP, True
            elif val < 16000 and prev_val >= 16000: action, pressed = PAGE_UP, False
        elif axis == sdl2.SDL_CONTROLLER_AXIS_TRIGGERRIGHT:
            if val > 16000 and prev_val <= 16000: action, pressed = PAGE_DOWN, True
            elif val < 16000 and prev_val >= 16000: action, pressed = PAGE_DOWN, False
    
    if action:
        _action_states[action] = pressed
        # Only return the action on "down" events to maintain compatibility with current screen logic
        return action if pressed else None
            
    return None
