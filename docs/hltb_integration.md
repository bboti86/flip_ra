# HowLongToBeat (HLTB) Integration Details

This document provides technical insights into how the RetroAchievements Manager integrates playtime data from HowLongToBeat.com.

## The Challenge: No Official API
HowLongToBeat does not provide a public API. Standard integration relies on scraping or unofficial handshakes. To keep the app lightweight and zero-dependency, we implemented a custom "handshake" engine in `core/hltb.py`.

## Technical Implementation

### 1. The Handshake Engine
To prevent being blocked by HLTB's dynamic protection, the app performs a modern HLTB handshake:
1.  **Dynamic ID Discovery**: Fetches the HLTB homepage to find the current Next.js `_app.js` bundle.
2.  **Key Extraction**: Analyzes the JavaScript bundle to extract the dynamic API key used for the `/api/search` endpoint.
3.  **JSON Search**: Performs a POST request to the internal search endpoint with a JSON payload mirroring the official website's behavior.

### 2. Matching Logic
Matching favorite games (from `pyui-favorites.json`) to HLTB entries uses a two-stage approach:
- **Title Search**: The HLTB API handles its own fuzzy search logic for the title.
- **Year Filtering**: When available, the app pulls the "Released" year from RetroAchievements (via `API_GetGameInfoAndUserProgress`) and passes it to HLTB to ensure that "God of War (2005)" isn't confused with "God of War (2018)".

### 3. Caching Strategy
To ensure the app remains fast and respects HLTB's server, all successful matches are cached:
- **Location**: `/mnt/SDCARD/Saves/hltb_cache.json`.
- **Content**: A map of game IDs to their three primary metrics (Main, Plus, 100%).

## UI Integration

### Dashboard "Backlog Health"
The dashboard aggregates the "Main Story" times for **every game** in your favorites list. This provides a "Total Backlog Hours" estimate at the top of your feed.

### Games "Shortest to Beat" Sort
Accessed via the **SELECT** button on the Games tab. This re-orders your favorite games based on their HLTB Main Story times.
- **Utility**: Helps the user pick their next "palate cleanser" game or commit to a long RPG.
- **Logic**: Games without HLTB data or cache entries are pushed to the bottom of the list during sort.

## Maintenance Note
HLTB occasionally updates their internal API structure. If "Shortest to Beat" sorting stops working or HLTB times disappear, it likely indicates that the dynamic key extraction in `core/hltb.py` needs to be updated to match a new HLTB website deployment.
