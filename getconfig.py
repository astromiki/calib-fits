#!/usr/bin/env python3

# =============================================================================
# Filename: getconfig.py
# Description:
#   This script reads and parses the config.ini file. It provides a convenient
#   way for the other scripts to access configuration parameters (like paths to
#   input data, output directories, or processing modes). We need it to ensure
#   consistent and organized handling of configuration data across all workflow
#   components.
# =============================================================================

import configparser
import sys
from pathlib import Path

def read_config(config_file="config.ini"):
    # Reads configuration from a config.ini file
    config_path = Path(config_file)

    # Check if the file exists
    if not config_path.exists():
        print(f"Error: Configuration file '{config_file}' not found.")
        return None  # Ensure we return None if the file is missing

    # Read config
    config = configparser.ConfigParser()
    config.read(config_path)

    if not config.sections():
        print(f"Error: Configuration file '{config_file}' is empty or invalid.")
        return None

    return config  # Ensure a valid object is returned

    # Print all sections and values
    print(f"Reading configuration from '{config_file}':\n")
    for section in config.sections():
        print(f"[{section}]")
        for key, value in config[section].items():
            print(f"{key} = {value}")
        print()

if __name__ == "__main__":
    # Allow optional filename argument
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.ini"
    read_config(config_file)

