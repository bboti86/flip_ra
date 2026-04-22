# RetroAchievements Manager: Logging Guide

This document outlines the standard logging practices implemented across the application using Python's built-in `logging` module.

## Centralized Logger Configuration

The application uses a centralized logger setup defined in `core/logger.py`. This ensures a consistent format and output destination for all modules.

### Log Output
- **Destination:** Standard Output (`sys.stdout`)
- **Formatting:** `[%(levelname)s] %(name)s: %(message)s`
- **Device Log File:** The output is captured by the main application wrapper (`launch.sh`) and redirected to `/mnt/SDCARD/App/RA_Manager/runtime.log`.

### Log Level Configuration
The global log level is dynamically configurable.
To change the log level, edit the root `settings.json` file and add or modify the `log_level` key:
```json
{
  "log_level": "DEBUG",
  "ra_username": "your_username"
}
```
If `log_level` is not specified, it defaults to `INFO`.

## Logging Levels and Usage

We use four main logging levels. When adding new logs to the application, adhere to these guidelines:

### 1. `logger.debug()`
**Purpose:** Granular information useful during development or deep troubleshooting.
**When to use:**
- Tracing variable values (e.g., `logger.debug(f"Resolved Stats: {stats}")`)
- Tracking file paths (e.g., `logger.debug(f"Successfully updated config: {path}")`)
- API response keys or raw data parsing

### 2. `logger.info()`
**Purpose:** General operational information confirming the application is working as expected.
**When to use:**
- Application startup/shutdown (e.g., `logger.info("--- RA Configurator Starting ---")`)
- State changes or screen transitions (e.g., `logger.info("Switching to Dashboard")`)
- Cache hits or routine API calls (e.g., `logger.info(f"Cache hit for game {game_id} progress")`)
- Significant user actions (e.g., `logger.info("Loaded 35 favorite games")`)

### 3. `logger.warning()`
**Purpose:** Indicating that something unexpected happened, but the application can still function.
**When to use:**
- Missing non-critical assets (e.g., `logger.warning("Missing font asset, text rendering will fail")`)
- External API rate limits or blocked connections where a retry might happen.

### 4. `logger.error()`
**Purpose:** Documenting errors that prevent a specific function or operation from completing.
**When to use:**
- Unhandled exceptions or library initialization failures (e.g., `logger.error(f"TTF_Init Error: {error_msg}")`)
- Failed API requests or network timeouts (e.g., `logger.error(f"API Exception: {e}")`)
- File system permission errors (e.g., `logger.error(f"Failed to update PPSSPP config: {e}")`)

## Implementation Example

To add logging to a new or existing module, follow this pattern:

```python
# Import the central logger setup
from core.logger import setup_logger

# Initialize a logger specifically for this module name
logger = setup_logger("my_module_name")

def my_function():
    logger.info("Starting my function")
    try:
        # Do something
        result = 10 / 2
        logger.debug(f"Calculation result: {result}")
    except Exception as e:
        logger.error(f"Failed calculation: {e}")
```

## Legacy Scripts
Note: Deployment scripts executed on the host PC (like `auto_push.py`) intentionally bypass the `core.logger` setup. They use standard `print()` statements with ANSI color codes to provide a more readable Command Line Interface output during the push process.
