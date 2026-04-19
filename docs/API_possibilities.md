

### **1. The "Retro Ratio" Heatmap**
Instead of a standard GitHub-style activity chart, color-code it by **Retro Ratio**.
* **The Concept:** If you earn a high-ratio (rare) achievement, the square is bright gold. Common achievements are dim white.
* **Why it’s interesting:** It visually separates your "grind" days (easy unlocks) from your "legendary" days (beating that one brutal Kaizo level).

### **2. Points toward Next Rank (Progression Gauge)**
The RA API provides your global rank and your total points. 
* **The Component:** A progress bar showing how many points you need to jump from, say, Rank #4,500 to #4,000. 
* **Pro Tip:** You can use the `getTopTenUsers` or user-neighbor endpoints to see the point gap between you and the players immediately above you. It turns the entire site into a competitive RPG.

### **3. "Unearned Potential" (The Backlog Tracker)**
This is a great motivator for your Miyoo Flip.
* **The Component:** A list of games you’ve started, showing a "Points Remaining" bar.
* **API Data:** Use `getGameInfoAndUserProgress`. It returns the total points in the set vs. what you’ve earned.
* **The Twist:** Sort this by **"Closest to Mastery."** If you have a game at 90% completion, it gets highlighted at the top to remind you to finish those last three achievements.

### **4. Hardcore vs. Softcore Split (The "Purity" Meter)**
Since you’re a power user, you probably prefer Hardcore mode.
* **The Component:** A donut chart showing your total points split between Hardcore (Gold) and Softcore (Silver).
* **Insight:** Many users have a "Softcore ghost" from their early days before they knew about Hardcore mode. Seeing that silver sliver shrink as you earn more Hardcore points is satisfying.

### **5. Console Dominance Radar**
The API provides the `system_id` for every game.
* **The Component:** A radar (spider) chart with axes for NES, SNES, Genesis, GBA, PS1, etc.
* **Why it’s interesting:** You might think you’re a Nintendo fan, but your dashboard might reveal you’ve actually mastered more Sega Genesis games. It’s a great way to see where your "nostalgia" actually lies.

### **6. The "Crown Jewel" (Rarest Unlock)**
* **The Component:** A dedicated slot on your dashboard for your single rarest achievement based on the **Retro Points** to **Standard Points** ratio.
* **API Data:** Look for the achievement with the highest `RetroRatio` in your `getUserRecentAchievements` or full unlock history. 
* **Display:** Show the achievement badge, the game title, and the percentage of users who have earned it (e.g., *"Unlocked by only 1.2% of players"*).

### **7. Mastery Wall (Badge Gallery)**
A simple but visually striking component.
* **The Component:** A grid of the 24x24 or 48x48 "Mastery" badges you've earned.
* **Automation:** Use the API to fetch the `image_name` for games where your `NumAwarded` equals the `NumAchievements`. On your Arch system, you could even script this to update your desktop wallpaper with a collage of these badges every time you master a game.

### **Example Data Mapping**
If you're scripting this (e.g., in Python or JS), here are the key keys to look for:

| Feature | Key API Field |
| :--- | :--- |
| **Rarity** | `RetroRatio` (Higher = Rarity) |
| **Mastery** | `NumAwarded` == `NumAchievements` |
| **Activity** | `DateAwarded` (Timestamp) |
| **System** | `ConsoleName` or `ConsoleID` |



feasibility:
Edited API_possibilities.md

Here is a feasibility estimate for bringing those awesome concepts to life natively on your **Miyoo Flip (SpruceOS)** using our current lightweight `PySDL2` architecture:

### 🟢 Highly Feasible (Can build quickly with high performance)

**2. Points toward Next Rank (Progression Gauge)**
*   **Feasibility: Very High**
*   **How:** We already hit the `GetUserSummary` endpoint, which gives us your rank and points. We just need to hit the neighbor endpoint to find the guy above you. Drawing a progress bar in SDL2 is incredibly easy (literally just `renderer.fill()` with two colored rectangles on top of each other).

**6. The "Crown Jewel" (Rarest Unlock)**
*   **Feasibility: High (Text Version)**
*   **How:** We can scan the API payload for the highest `RetroRatio` number. Displaying the title, percentage, and game name is trivial. *Caveat:* If you want the actual image badge displayed, we have to download the `.png` and decode it with `sdl2.sdlimage`, which adds a slight loading delay, but is very doable.

**4. The "Purity" Meter (Hardcore vs Softcore)**
*   **Feasibility: High (As a Bar Chart)**
*   **How:** Drawing a literal *Donut Chart* in raw SDL2 is notoriously annoying (requires plotting circles with trigonometry). However, drawing a dual-colored horizontal **Progress Bar** (Gold for Hardcore, Silver for Softcore) is trivial and visually striking. 

---

### 🟡 Medium Feasibility (Requires careful memory/network management)

**3. "Unearned Potential" (The Backlog Tracker)**
*   **Feasibility: Medium**
*   **How:** The UI part is easy (a scrolling text list). The problem is the network. The Miyoo's Wi-Fi chip is slow. If you have 50 games in your backlog, making 50 separate API calls to `getGameInfoAndUserProgress` will freeze the device for 10-20 seconds. We would need to aggressively cache this data locally in `settings.json` and only fetch it once a week in the background.

**7. Mastery Wall (Badge Gallery)**
*   **Feasibility: Medium**
*   **How:** PySDL2 can render images, but downloading a 5x5 grid of PNGs over the Miyoo's Wi-Fi will take time. We would absolutely need to build an image cache system directly on the SD card so we only download an image once. It's highly feasible, but requires building a robust, async file-downloader first.

---

### 🔴 Low Feasibility (Not recommended for raw PySDL2 on Miyoo)

**1. The "Retro Ratio" Heatmap**
*   **Feasibility: Low**
*   **How:** The API call required to get an entire year of daily achievement data is massive. Parsing that much JSON on the Miyoo's CPU in Python, calculating the dates, and then drawing 365 tiny colored squares on a 640x480 screen would result in serious performance lag and UI clutter. 

**5. Console Dominance Radar**
*   **Feasibility: Low (As a Radar Chart)**
*   **How:** Similar to the donut chart, drawing a polygon-based spider web chart natively in SDL2 requires a custom geometry rendering engine. We don't have libraries like `matplotlib` or `Chart.js` here. 
*   **Alternative:** Extremely feasible if we just display it as a sorted text list or standard bar charts (e.g. `SNES: 5000pts | GBA: 3000pts`).

### **Implementation Status**

The following features have been successfully implemented:

*   ✅ **Progression Gauge**: Dynamic rank and point tracking.
*   ✅ **Purity Meter**: Hardcore vs. Softcore points split visualization.
*   ✅ **Crown Jewel**: Automatic highlighting of your rarest recent achievement with badge preview.
*   ✅ **Console Dominance**: Ranked breakdown of Top 3 systems using dual bar charts (Games vs. Achievements).
*   ✅ **Fluid Navigation**: Hardware-accelerated pixel scrolling and clipping for all list-heavy screens.

---

### **Future Roadmap Ideas**

With the successful implementation of the async background syncing engine and local `tar` image caching, the following features remain highly feasible for future development:

#### **1. The Mastery Wall 🏆**
*   **Feasibility: Very High**
*   **How:** A dedicated visual grid on the Stats screen that fetches official Game Icons for games where `NumAwarded == NumAchievements`. Displays a beautiful gallery of 100% completed games.

#### **2. The Backlog Tracker (Closest to Mastery) 📈**
*   **Feasibility: High**
*   **How:** Leverage the background syncing engine to silently scan games and list the ones where completion is at 90%+ at the bottom of the Stats screen, motivating the user to finish them.

#### **3. The "Retro Ratio" Heatmap 🔥**
*   **Feasibility: Medium**
*   **How:** A GitHub-style activity grid color-coded by the rarity (Retro Ratio) of achievements earned each day. Requires careful handling of the potentially large historical data payload.