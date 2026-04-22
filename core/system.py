import os

class SystemManager:
    @staticmethod
    def get_os_type():
        if os.path.exists("/mnt/SDCARD/spruce"):
            return "SPRUCE"
        if os.path.exists("/mnt/SDCARD/miyoo") or os.path.exists("/mnt/SDCARD/.tmp_update"):
            return "ONION"
        return "GENERIC"

    @staticmethod
    def get_favorites_path():
        os_type = SystemManager.get_os_type()
        if os_type == "SPRUCE":
            return "/mnt/SDCARD/Saves/pyui-favorites.json"
        elif os_type == "ONION":
            # OnionOS standard favorites path
            return "/mnt/SDCARD/Saves/CurrentProfile/favorites.json"
        
        # Fallback to local file for development/testing
        if os.path.exists("pyui-favorites.json"):
            return "pyui-favorites.json"
        return "favorites.json"

    @staticmethod
    def get_system_map():
        # Default map (SpruceOS names)
        base_map = {
            "ARCADE": 27, "SFC": 3, "SNES": 3, "GBA": 5, "GB": 4, "GBC": 6,
            "MD": 1, "GENESIS": 1, "FC": 7, "NES": 7, "PS": 12, "PSX": 12,
            "N64": 2, "NDS": 18, "PSP": 41, "PCE": 8, "TG16": 8
        }
        
        os_type = SystemManager.get_os_type()
        if os_type == "ONION":
            # OnionOS often uses lowercase or full names, we can add them here
            base_map.update({
                "sfc": 3, "snes": 3, "gba": 5, "gb": 4, "gbc": 6,
                "md": 1, "genesis": 1, "fc": 7, "nes": 7, "ps": 12,
                "n64": 2, "nds": 18, "psp": 41, "pce": 8
            })
            
        return base_map
