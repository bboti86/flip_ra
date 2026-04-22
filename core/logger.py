import logging
import json
import os
import sys

def setup_logger(name):
    """
    Sets up a configured logger.
    The log level is determined by the 'log_level' key in settings.json.
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if setup_logger is called multiple times for the same name
    if not logger.handlers:
        # Load config to determine level
        log_level_str = "INFO"
        config_path = os.path.join(os.path.dirname(__file__), '..', 'settings.json')
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    log_level_str = config.get("log_level", "INFO").upper()
        except Exception:
            pass # Fallback to INFO if any error occurs reading settings

        # Map string to logging level
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        level = level_map.get(log_level_str, logging.INFO)
        
        logger.setLevel(level)

        # Create console handler (stdout goes to runtime.log via launch.sh)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)

        # Create formatter and add it to the handler
        formatter = logging.Formatter('[%(levelname)s] %(name)s: %(message)s')
        ch.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(ch)

    return logger
