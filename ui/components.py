import sdl2
import sdl2.ext
import sdl2.sdlttf
import sdl2.sdlimage
import os

_texture_cache = {}

def draw_image(renderer, path, x, y, w=None, h=None):
    if not path or not os.path.exists(path):
        return
    
    if path in _texture_cache:
        texture = _texture_cache[path]
    else:
        surface = sdl2.sdlimage.IMG_Load(path.encode('utf-8'))
        if not surface:
            return
        texture = sdl2.SDL_CreateTextureFromSurface(renderer.sdlrenderer, surface)
        sdl2.SDL_FreeSurface(surface)
        if not texture:
            return
        _texture_cache[path] = texture

    # Get width/height if not provided
    if w is None or h is None:
        query_w, query_h = sdl2.Uint32(), sdl2.Uint32()
        sdl2.SDL_QueryTexture(texture, None, None, query_w, query_h)
        w = w or query_w.value
        h = h or query_h.value
        
    rect = sdl2.SDL_Rect(int(x), int(y), int(w), int(h))
    sdl2.SDL_RenderCopy(renderer.sdlrenderer, texture, None, rect)

def render_text(renderer, font, text, x, y, fg_color, center=False):
    if not text:
        return None
    
    color = sdl2.SDL_Color(fg_color[0], fg_color[1], fg_color[2], 255)
    surface = sdl2.sdlttf.TTF_RenderUTF8_Blended(font, text.encode('utf-8'), color)
    if not surface:
        return None

    texture = sdl2.SDL_CreateTextureFromSurface(renderer.sdlrenderer, surface)
    if texture:
        w, h = surface.contents.w, surface.contents.h
        if center:
            x = x - w // 2
        rect = sdl2.SDL_Rect(int(x), int(y), w, h)
        sdl2.SDL_RenderCopy(renderer.sdlrenderer, texture, None, rect)
        sdl2.SDL_DestroyTexture(texture)

    sdl2.SDL_FreeSurface(surface)

def render_text_shadow(renderer, font, text, x, y, fg_color, shadow_color=(0,0,0), center=False, shadow_offset=2):
    """Renders text with a drop-shadow for a premium retro feel."""
    if not text: return
    # Draw shadow first
    render_text(renderer, font, text, x + shadow_offset, y + shadow_offset, shadow_color, center)
    # Draw main text
    render_text(renderer, font, text, x, y, fg_color, center)

def draw_panel(renderer, x, y, w, h, bg_color=(20, 20, 30, 240), border_color=(60, 60, 80)):
    """Draws a premium dark panel with a subtle border."""
    # Main background (supports alpha if blend mode is set)
    renderer.fill((x, y, w, h), sdl2.ext.Color(*bg_color))
    # Border
    renderer.draw_rect((x, y, w, h), sdl2.ext.Color(*border_color))
    # Inner highlight to give depth
    renderer.draw_rect((x+1, y+1, w-2, h-2), sdl2.ext.Color(40, 40, 50, 100))

def draw_selector(renderer, x, y, w, h, color=(0, 200, 255)):
    """Draws a glowing retro selector box around an item."""
    # Outer glow (thin, lower alpha)
    renderer.draw_rect((x-2, y-2, w+4, h+4), sdl2.ext.Color(color[0], color[1], color[2], 100))
    renderer.draw_rect((x-1, y-1, w+2, h+2), sdl2.ext.Color(color[0], color[1], color[2], 180))
    # Inner bright box
    renderer.draw_rect((x, y, w, h), sdl2.ext.Color(*color))
    # Fill slightly to make it pop
    renderer.fill((x, y, w, h), sdl2.ext.Color(color[0], color[1], color[2], 40))

class TextInput:
    def __init__(self, x, y, width, height, font, bg_color=(50,50,50), fg_color=(255,255,255), is_password=False):
        self.rect = sdl2.SDL_Rect(int(x), int(y), int(width), int(height))
        self.font = font
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.is_password = is_password
        self.text = ""
        self.active = False
                
    def draw(self, renderer):
        color = (100,100,100) if self.active else self.bg_color
        renderer.fill((self.rect.x, self.rect.y, self.rect.w, self.rect.h), sdl2.ext.Color(*color))
        
        display_text = "*" * len(self.text) if self.is_password else self.text
        # Optional cursor
        if self.active: display_text += "_"
        
        render_text(renderer, self.font, display_text, self.rect.x + 10, self.rect.y + 10, self.fg_color)


class OnScreenKeyboard:
    def __init__(self, font):
        self.font = font
        self.keys_normal = [
            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "="],
            ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p", "[", "]"],
            ["a", "s", "d", "f", "g", "h", "j", "k", "l", ";", "'", "\\"],
            ["z", "x", "c", "v", "b", "n", "m", ",", ".", "/", "BACK"],
            ["SHIFT", "_", "@", "SPACE", "DONE"]
        ]
        self.keys_shifted = [
            ["!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "_", "+"],
            ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "{", "}"],
            ["A", "S", "D", "F", "G", "H", "J", "K", "L", ":", '"', "|"],
            ["Z", "X", "C", "V", "B", "N", "M", "<", ">", "?", "BACK"],
            ["SHIFT", "_", "@", "SPACE", "DONE"]
        ]
        self.shifted = False
        self.cx = 0
        self.cy = 0
        self.base_x = 22
        self.base_y = 260
        self.key_w = 44
        self.key_h = 40

    def get_layout(self):
        return self.keys_shifted if self.shifted else self.keys_normal

    def handle_action(self, action):
        layout = self.get_layout()
        if action == "UP":
            self.cy = max(0, self.cy - 1)
            self.cx = min(len(layout[self.cy]) - 1, self.cx)
        elif action == "DOWN":
            self.cy = min(len(layout) - 1, self.cy + 1)
            self.cx = min(len(layout[self.cy]) - 1, self.cx)
        elif action == "LEFT":
            self.cx = max(0, self.cx - 1)
        elif action == "RIGHT":
            self.cx = min(len(layout[self.cy]) - 1, self.cx + 1)
        elif action == "ACCEPT":
            val = layout[self.cy][self.cx]
            if val == "SHIFT":
                self.shifted = not self.shifted
                return None
            return val
        elif action == "START":
            return "DONE"
        elif action == "CANCEL":
            return "DONE_CANCEL"
        return None

    def draw(self, renderer):
        renderer.fill((0, self.base_y - 10, 640, 480 - self.base_y + 10), sdl2.ext.Color(30, 30, 40))
        layout = self.get_layout()
        
        for r, row in enumerate(layout):
            rx = self.base_x
            for c, key in enumerate(row):
                # Adjust width for special keys
                w = self.key_w
                if key in ["BACK", "SHIFT", "DONE"]:
                    w = self.key_w * 2 + 5
                elif key == "SPACE":
                    w = self.key_w * 3 + 10

                ry = self.base_y + r * self.key_h + (r * 5)
                
                bg_color = (60, 60, 200) if (r == self.cy and c == self.cx) else (50, 50, 50)
                if key == "SHIFT" and self.shifted:
                    bg_color = (100, 100, 250) if (r == self.cy and c == self.cx) else (80, 80, 220)
                
                renderer.fill((rx, ry, w, self.key_h), sdl2.ext.Color(*bg_color))
                
                text_x_offset = w // 2
                render_text(renderer, self.font, key, rx + text_x_offset, ry + 10, (255, 255, 255), center=True)
                
                rx += w + 5
