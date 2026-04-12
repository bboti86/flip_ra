#!/bin/sh
# title=RA Manager
# icon=icon.png
# description=RetroAchievements Manager
SCRIPT_DIR=$(dirname "$0")

# Source SpruceOS helper functions to use their native SDL2 equipped python
if [ -f "/mnt/SDCARD/spruce/scripts/helperFunctions.sh" ]; then
    . /mnt/SDCARD/spruce/scripts/helperFunctions.sh
    PYTHON_EXEC=$(get_python_path)
    
    # Export DLL path depending on the platform discovered by Spruce
    if [ "$PLATFORM" = "Flip" ]; then
        export PYSDL2_DLL_PATH="/mnt/SDCARD/App/PyUI/dll"
    elif [ "$PLATFORM" = "A30" ]; then
        export PYSDL2_DLL_PATH="/mnt/SDCARD/spruce/a30/sdl2"
    elif [ "$PLATFORM" = "Brick" ] || [ "$PLATFORM" = "SmartPro" ] || [ "$PLATFORM" = "SmartProS" ]; then
        export PYSDL2_DLL_PATH="/mnt/SDCARD/spruce/brick/sdl2"
    elif [ "$PLATFORM" = "MiyooMini" ]; then
        export PYSDL2_DLL_PATH="/mnt/SDCARD/spruce/miyoomini/lib"
    elif [ "$PLATFORM" = "Pixel2" ]; then
        export PYSDL2_DLL_PATH="/usr/lib"
    else
        # Fallback to standard Anbernic / Linux paths
        export PYSDL2_DLL_PATH="/usr/lib/aarch64-linux-gnu/"
        export LD_LIBRARY_PATH="/usr/lib32:/usr/lib:/mnt/vendor/lib:$LD_LIBRARY_PATH"
    fi
else
    # Fallback to default python
    PYTHON_EXEC="python"
fi

# Setup python path to use the bundled libs
export PYTHONPATH="$SCRIPT_DIR/libs:$PYTHONPATH"

cd "$SCRIPT_DIR"

# Execute the application and pipe all output (and errors) to a runtime log
"$PYTHON_EXEC" main.py > "$SCRIPT_DIR/runtime.log" 2>&1
