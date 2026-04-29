# SpruceOS Application Development Guide

This guide captures everything we've learned about building native, high-performance, and visually appealing applications for the Miyoo Flip running SpruceOS. These patterns can be reused as a blueprint for bootstrapping future projects on similar low-power retro handhelds.

## 1. Architecture of SpruceOS Apps

SpruceOS devices are low-power and have limited RAM. They require a lightweight, hardware-accelerated approach to application development.

*   **PySDL2 Foundation**: We bypass standard Python GUI frameworks (like Tkinter or PyQt) in favor of `PySDL2`. It provides direct access to the hardware renderer (`sdl2.SDL_RENDERER_ACCELERATED`) and native GameController API.
*   **Non-Blocking Operations**: The Miyoo will freeze if the main SDL rendering loop is blocked by network requests or heavy I/O. All long-running operations (like API calls or file parsing) must be wrapped in background threads: `threading.Thread(target=_task, daemon=True).start()`.
*   **Aggressive Caching**: To minimize network overhead and save battery, use local JSON caching (e.g., `api_cache.json`, `match_cache.json`).
*   **Input Handling**: Avoid relying solely on `SDL_KEYDOWN`. Custom firmware often maps the D-Pad to analog axes. Our input module (`core/input.py`) checks `SDL_CONTROLLERAXISMOTION` with thresholds (e.g., `< -16000` or `> 16000`) for the D-Pad and maintains an `_action_states` dictionary for continuous scrolling.

## 2. The Custom On-Screen Keyboard (OSK)

Because the Miyoo Flip lacks a physical keyboard, we implemented a custom, highly responsive virtual keyboard (`ui/components.py` -> `OnScreenKeyboard`).

*   **Grid System**: The keyboard is structured as a 2D array of keys (both a `keys_normal` and `keys_shifted` layout).
*   **Coordinate Navigation**: D-Pad inputs adjust `self.cx` (column) and `self.cy` (row) coordinates. We use `min()` and `max()` bounds checking to keep the cursor within the grid layout.
*   **Dynamic Key Sizing**: Special keys like `SPACE`, `SHIFT`, `BACK`, and `DONE` are rendered dynamically wider (`w = self.key_w * 3 + 10`) to provide a familiar QWERTY feel.
*   **Integration**: The OSK seamlessly integrates with `TextInput` components. When an input field becomes active, D-Pad events are routed to the OSK instead of standard UI navigation.

## 3. File System Specifics & Persistence

Understanding where things live on SpruceOS is crucial for maintaining state and modifying system emulators.

*   **App Directory**: Applications live in `/mnt/SDCARD/App/`. Our app sits in `/mnt/SDCARD/App/RA_Manager`.
*   **Persistence Layer**: To avoid data loss during updates, user state (like `settings.json`, runtime logs, and cache files) is stored in the same folder as the app and meticulously preserved during the auto-push cycle.
*   **Emulator Configs**: The app integrates tightly with other system components by reading and modifying their config files (e.g., `retroarch.cfg` for RetroArch and `ppsspp.ini` for PPSSPP), injecting credentials without requiring the user to open those emulators' native menus.

## 4. The `auto_push.py` Deployment Script

Developing directly on the Miyoo via SD-card swapping is slow. We created `auto_push.py` to orchestrate over-the-air (OTA) deployments.

*   **Zero-Friction Build**: The script cleans the local workspace, creates a pristine `deploy/` folder, and strips out unnecessary caches (`__pycache__`).
*   **State Preservation via SCP**: It connects to the device via SSH (IP: `10.0.2.1`, default credentials `spruce`/`happygaming`), and *pulls down* the latest `settings.json`, logs, and cache files to sync the local PC.
*   **Surgical Updates**: Instead of deleting the whole app folder on the device (which would wipe assets and configs), it surgically removes the code directories (`core`, `ui`, `libs`, `main.py`) via SSH command `rm -rf`.
*   **Fast Push**: It then pushes the new code using `paramiko` and `scp`, making iteration incredibly fast.

## 5. GUI Aesthetics & "Premium" Design

To ensure the app looks professional and native, we built custom drawing primitives in `ui/components.py`:

*   **Premium Dark Panels (`draw_panel`)**: Instead of flat colors, we use semi-transparent dark backgrounds (`rgba(20, 20, 30, 240)`) with subtle borders and an inner highlight rectangle. This gives UI elements physical depth.
*   **Text Rendering (`render_text_shadow`)**: Standard TTF rendering looks flat. Every piece of text is rendered with a drop-shadow offset, making it pop against the background and feel like a polished retro interface.
*   **Glowing Selectors (`draw_selector`)**: Active elements are highlighted using nested, semi-transparent rectangles with varying alpha values (e.g., `100` then `180` then an inner solid box). This creates a "glowing" neon effect.
*   **Standardized Help Footers**: Every screen features a consistent footer (`L1/R1: Tab | D-Pad: Select...`) ensuring the user always knows the exact hardware controls available at any given time.
*   **Hardware Clipping**: We use `sdl2.SDL_RenderSetClipRect` to bound scrollable lists inside a specific region, ensuring text smoothly cuts off rather than bleeding into the headers and footers.
