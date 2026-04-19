# 🏆 RetroAchievements Manager for SpruceOS

A native, lightweight, graphical management tool built in **PySDL2** for the Miyoo Flip (and other SpruceOS devices). 

This app allows you to securely manage your RetroAchievements credentials, sync deep RetroArch preferences across multiple platform cores, and track your gaming milestones directly from your handheld device—without ever needing to edit text configuration files manually.

![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)
![Platform](https://img.shields.io/badge/platform-Miyoo%20Flip%20%7C%20SpruceOS-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## ✨ Key Features

*   **🔒 Secure Credential Management**: Safely enter your Username, Password, and Web API Key. Your sensitive data is masked during input and saved securely to a local `settings.json`.
*   **⚙️ Universal Config Injection**: With a press of a button, inject your credentials and preferences into *all* SpruceOS platform-specific RetroArch configuration files (`.cfg`) and PPSSPP (`.ini`) configs at once.
*   **🛠️ Deep Preference Toggles**: Turn on **Hardcore Mode**, toggle unlock sounds, adjust the position of notification anchors, and more directly from the app.
*   **🩺 Diagnostics & Logging**:
    *   **Automatic Logging**: All application output and errors are captured in `runtime.log`.
    *   **Log Rotation**: Keeps history for the last 3 sessions.
    *   **Auto-Sync**: The `auto_push.py` script automatically downloads these logs and preserves your image cache securely.
*   **⚡ Smart Caching & Quality of Life**: 
    *   **State Memory**: The app remembers exactly which tab you left off on and restores it instantly on next launch.
    *   **API Caching**: To respect device battery and the RetroAchievements API limits, server responses are cached locally.
*   **🏎️ Fluid Navigation**: Experience smooth, high-speed browsing of large lists:
    *   **Hardware Clipping**: Native PySDL2 clip rects provide buttery-smooth pixel scrolling.
    *   **Continuous Scrolling**: Hold Up/Down to scroll automatically.
    *   **Wrap-around Logic**: Seamlessly cycle from the top to the bottom of lists.
    *   **Page Jumps**: Use L2/R2 to jump whole pages at a time in long lists.

---

## 🖼️ Application Screens

The application is split into five fast-rendering, hardware-accelerated screens:

### 1. Credentials (Auth)
The core login screen. Enter your RetroAchievements Username, Password (required by RetroArch), and Web API Key (required for advanced user stats). 

### 2. Preferences (Settings)
A toggle menu to adjust how RetroAchievements behaves inside games.
- Enable/Disable **Hardcore Mode**.
- Set **Appearance Anchors** (Top-Left, Bottom-Right, etc.) to keep UI elements from blocking vital HUD components.
- Toggle Challenge Indicators, Auto-Screenshots, and Unlock Sounds.

### 3. Recent Achievements (Dashboard)
Displays a cleanly formatted, pixel-scrollable list of every achievement you have unlocked in the past week, dynamically loading your locally cached achievement badges for a premium UI experience.

### 4. Favorite Games (Games)
Directly reads your SpruceOS `pyui-favorites.json` and connects them to RetroAchievements!
- **Dynamic Matching**: Fuzzy-matches your local ROM names against the RA database.
- **Icon Caching**: Downloads and caches official square Game Icons for an enhanced list view.
- **Global Badge Sync**: An autonomous background worker iterates through all your favorites and batch-downloads missing assets for offline browsing.
- **HowLongToBeat**: Sort your backlog by "Shortest to Beat" using our custom HLTB engine.

### 5. Profile Stats (Stats)
The gamification layer. Generates custom tracking bars utilizing mathematical calculations on the raw API data to visualize your rank progression, "purity" ratio, and your crowning achievement. 
- **Progression Gauge**: Distance to your next global rank milestone.
- **Completionist Rank**: Skill title based on your mastery rate.
- **Hardcore Purity**: Your ratio of Hardcore vs. Softcore points.
- **Mastery Wall**: A grid of icons for your 100% mastered games.
- **Crown Jewel**: Your rarest recent achievement with badge preview.
- **Console Dominance**: Dual-bar charts for your top 5 systems (Games Played vs. Achievements Earned).
- **Backlog Tracker**: Your top 5 games closest to mastery (10%+ completion).

---

## 🎮 Controls

The app uses standard SDL GameController mappings natively compatible with the Miyoo handhelds:

| Action | Control | Description |
| :--- | :--- | :--- |
| **Cycle Tabs** | `L1` / `R1` | Seamlessly cycle between Auth ↔ Settings ↔ Recent ↔ Games ↔ Stats. |
| **Navigate** | `D-Pad` | Move between items. **Hold** for continuous scrolling. |
| **Page Up / Down** | `L2` / `R2` | Scroll through entire pages of achievements or games. |
| **Wrap-around** | `D-Pad UP/DOWN` | Cycling from the top of a list jumps to the bottom. |
| **Select / Toggle** | `A` Button | Open keyboard for text fields, view a game's achievements, or toggle booleans. |
| **Go Back** | `B` Button | Cancel input or return to the previous screen. |
| **Global Badge Sync**| `Start` | In the Favorite Games view, press Start to batch download all game icons and badges. |
| **Save / Sync** | `Start` | In Auth/Settings, press Start to save preferences and push configurations. |

---

## 📥 Installation & Deployment

Because this is a native SpruceOS application, no external Python environments or complex dependencies are needed beyond the pre-installed PySDL2 engine.

**Manual SD Card Installation:**
1. Download the latest release from the Releases page.
2. Extract the contents.
3. Place the `flip_ra` folder into the `App` directory on your Miyoo SD card (e.g., `/mnt/SDCARD/App/flip_ra/`).
4. Ensure `launch.sh` points to `main.py`.

**Developer Deployment (via SSH):**
If you are modifying the code, use the included `auto_push.py` script to rapidly sync changes to your device over Wi-Fi. 
*Note: This script intelligently preserves your `settings.json` and cached image assets securely so you do not lose data during updates.*
```bash
./auto_push.py
```

---

## 🗺️ Roadmap / Planned Features

- [ ] **🔥 Retro Ratio Heatmap**: A GitHub-style activity grid color-coded by achievement rarity.
- [ ] **⏳ Total Backlog Hours**: Sum up HLTB times to estimate how long to clear your favorites list.
- [ ] **☁️ Cloud Save Backup**: Automated syncing of `settings.json` and cache to a remote backup service.

---

## 📚 Documentation & Contributing

For developer insights and brainstorming data around the API structures and SpruceOS retroarch configurations used during the creation of this app, check out the [docs folder](./docs).

Contributions, issues, and feature requests are welcome! If you find a SpruceOS platform configuration file that isn't currently targeted by the injection engine, feel free to submit a Pull Request modifying `core/retroachievements.py`.

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

*Not officially affiliated with RetroAchievements.org.*
