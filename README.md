# 🏆 RetroAchievements Manager for SpruceOS

A native, lightweight, graphical management tool built in **PySDL2** for the Miyoo Flip (and other SpruceOS devices). This app allows you to securely manage your RetroAchievements credentials, sync deep RetroArch preferences across multiple platform cores, and track your gaming milestones directly from your handheld device—without ever needing to edit text configuration files manually.

![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)
![Platform](https://img.shields.io/badge/platform-Miyoo%20Flip%20%7C%20SpruceOS-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

*   **🔒 Secure Credential Management**: Safely enter your Username, Password, and Web API Key. Your sensitive data is masked during input and saved securely to a local `settings.json`.
*   **⚙️ Universal Config Injection**: With a press of a button, inject your credentials and preferences into *all* SpruceOS platform-specific RetroArch configuration files (`.cfg`) and PPSSPP (`.ini`) configs at once.
*   **🛠️ Deep Preference Toggles**: Turn on **Hardcore Mode**, toggle unlock sounds, adjust the position of notification anchors, and more directly from the app.
*   **📊 Gamified Profile Stats**: Check your progress without launching a browser:
    *   **Dashboard**: View recent achievements and tracking milestones.
    *   **Games & Achievements**: Browse progress for your favorite games. Includes background badge caching and a nostalgic ASCII progress bar.
    *   **Progression Gauge**: A visual bar tracking the points you need to hit your next global milestone.
    *   **Purity Meter**: A Gold/Silver ratio bar showing your Hardcore vs. Softcore points split.
    *   **Crown Jewel**: Automatically highlights your single rarest recent achievement based on `RetroRatio` rarity.
*   **🩺 Diagnostics & Logging**:
    *   **Automatic Logging**: All application output and errors are captured in `runtime.log`.
    *   **Log Rotation**: Keeps history for the last 3 sessions (`runtime.log`, `.1`, `.2`).
    *   **Auto-Sync**: The `auto_push.py` script automatically downloads these logs from your device for easy remote debugging.
*   **⚡ Smart Caching**: To respect device battery and the RetroAchievements API limits, server responses are cached locally for 1 hour.
*   **🏎️ Fluid Navigation**: Experience smooth, high-speed browsing of large game lists:
    *   **Continuous Scrolling**: Hold Up/Down to scroll automatically after a short delay.
    *   **Wrap-around Logic**: Seamlessly cycle from the top to the bottom of lists (and vice versa).
    *   **Page Jumps**: Use L2/R2 to jump whole pages at a time in long lists.

---

## 🎮 Controls

The app uses standard SDL GameController mappings natively compatible with the Miyoo handhelds:

| Action | Control | Description |
| :--- | :--- | :--- |
| **Cycle Tabs** | `L1` / `R1` | Seamlessly cycle between Auth ↔ Settings ↔ Dashboard ↔ Stats. |
| **Navigate** | `D-Pad` | Move between items. **Hold** for continuous scrolling. |
| **Page Up / Down** | `L2` / `R2` | Scroll through entire pages of achievements or games. |
| **Wrap-around** | `D-Pad UP/DOWN` | Cycling from the top of a list jumps to the bottom. |
| **Select / Toggle** | `A` Button | Open keyboard for text fields, or toggle YES/NO booleans. |
| **Go Back** | `B` Button | Cancel input or return to the previous screen. |
| **Save / Sync** | `Start` | Save preferences and push configurations. |

---

## 📥 Installation

Because this is a native SpruceOS application, no external Python environments or complex dependencies are needed beyond the pre-installed PySDL2 engine.

**Manual SD Card Installation:**
1. Download the latest release from the Releases page.
2. Extract the contents.
3. Place the `flip_ra` folder into the `App` directory on your Miyoo SD card (e.g., `/mnt/SDCARD/App/flip_ra/`).
4. Ensure `launch.sh` (if applicable) or your specific SpruceOS App invoker points to `main.py`.

**Developer Deployment (via SSH):**
If you are modifying the code, use the included `auto_push.py` script to rapidly sync changes to your device over Wi-Fi:
```bash
./auto_push.py
```
*(This script intelligently preserves your `settings.json` so you do not lose your credentials during updates).*

---

## 🖼️ Application Structure

The application is split into four distinct, fast-rendering screens:

### 1. Credentials (AuthScreen)
The core login screen. Enter your RetroAchievements Username, Password (required by RetroArch), and Web API Key (required for pulling advanced user stats). 

### 2. Preferences (SettingsScreen)
A toggle menu to adjust how RetroAchievements behaves inside games.
- Enable/Disable **Hardcore Mode**.
- Set **Appearance Anchors** (Top-Left, Bottom-Right, etc.) to keep UI elements from blocking vital HUD components.
- Toggle Challenge Indicators, Auto-Screenshots, and Unlock Sounds.

### 3. Dashboard (DashboardScreen)
Displays a cleanly formatted list of every achievement you have unlocked in the past week (10,080 minutes), complete with game titles and unlock dates.

### 4. Profile Stats (StatsScreen)
The gamification layer. Generates custom tracking bars utilizing mathematical calculations on the raw API data to visualize your rank progression, "purity" ratio, and your crowning achievement.

---

## 📚 Documentation

For developer insights and brainstorming data around the API structures and SpruceOS retroarch configurations used during the creation of this app, check out the [docs folder](./docs):
- [API Data Endpoints & Stats Ideas](./docs/API_possibilities.md)
- [SpruceOS RetroArch Config Breakdown](./docs/config_description.md)
## 🗺️ Roadmap / Planned Features
- [ ] **📈 HowLongToBeat Integration**: Playtime estimates and "Time to Beat" library insights.
- [ ] **☁️ Cloud Save Backup**: Automated syncing of `settings.json` and cache to a remote backup service.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! 
If you find a SpruceOS platform configuration file that isn't currently targeted by the injection engine, feel free to submit a Pull Request modifying `core/retroachievements.py`.

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

---
*Not officially affiliated with RetroAchievements.org.*
