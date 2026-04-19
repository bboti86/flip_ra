import os
import sys

# Add project root to path so we can import core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import hltb

def test():
    test_games = [
        "LocoRoco",
        "Castlevania: Aria of Sorrow",
        "God of War"
    ]
    
    print("--- HLTB Scraper Local Test ---")
    for game in test_games:
        print(f"\nSearching for: {game}...")
        result = hltb.get_game_times(game)
        if result:
            print(f"✅ Found: {result['title']}")
            print(f"   Main: {result['main']}h")
            print(f"   Plus: {result['plus']}h")
            print(f"   100%: {result['100']}h")
        else:
            print(f"❌ No results found for {game}")

if __name__ == "__main__":
    test()
