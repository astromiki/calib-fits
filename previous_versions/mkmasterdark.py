#!/usr/bin/env python3

# =============================================================================
# Filename: mkmasterdark.py
# Description:
#   This script is responsible for creating a master dark frame from multiple
#   individual dark frames. It reads a set of raw dark images, combines them
#   (by median), and outputs a single master dark. We need this master dark in
#   order to subtract thermal noise from our science frames more accurately.
#
#   This version uses config.ini values rather than the FITS header for image type
#   or other calibration parameters.
#   - param dark_files: List of paths to FITS files known to be dark frames.
#   - param output_filename: Where to write the resulting master dark.
#   - param config: A ConfigParser or dictionary-like object holding calibration settings.
#   - return: The path to the newly created master dark file.
#
# =============================================================================

## - test lines


import os
import sys
import numpy as np
from astropy.io import fits
from astropy.stats import sigma_clip
from astropy.visualization import ZScaleInterval
from pathlib import Path
## (old) import getconfig
import calib_config
import argparse
import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------
# Function: find_dark_frames
# Description:
#   OLD: Reads dark frames by checking the FITS header "IMAGETYP" directly.
#   NEW: Reads the expected dark frame pattern from config.ini and then compares.
# ---------------------------------------------------------------------------
def find_dark_frames(paths, config):
    # NEW: Retrieve the dark frame pattern from config.ini (e.g., "dark")
    pattern = config.get("DARK_FRAMES", "pattern", fallback="dark").lower()
    dark_files = []
    for path in paths:
        if os.path.isdir(path):
            # Recursively search directories.
            for root, dirs, files in os.walk(path):
                for file in files:
                    if pattern in file.lower():
                        dark_files.append(os.path.join(root, file))
        elif os.path.isfile(path):
            if pattern in os.path.basename(path).lower():
                dark_files.append(path)
    return dark_files


# ---------------------------------------------------------------------------
# Function: make_master_dark
# Description:
#   Creates a master dark frame from multiple dark frames.
#   Reads dark correction settings from config.ini.
# ---------------------------------------------------------------------------
def make_master_dark(dark_files, output_filename, config):
    # NEW: Check if dark correction is enabled in config.ini.
    dark_correction_enabled = config["IMAGE_PROCESSING"].getboolean("dark_correction", fallback=True)
    if not dark_correction_enabled:
        print("Dark correction is disabled in config; skipping master dark generation.")
        return None

    # NEW: Retrieve the dark correction method from config.ini.
    method = config["IMAGE_PROCESSING"].get("dark_correction_method", "EqualExposure")

    # Read all dark frame data.
    dark_data_arrays = []
    for file in dark_files:
        with fits.open(file) as hdul:
            data = hdul[0].data.astype(np.float32)
            dark_data_arrays.append(data)

    # Combine dark frames based on the specified method.
    if method == "EqualExposure":
        print("Applying equal exposure method for dark combination.")
        master_dark = np.median(dark_data_arrays, axis=0)
    else:
        # OLD: print("Error: Unsupported dark correction method.")
        # NEW: Use median as a fallback if unsupported method encountered.
        print("Error: Unsupported dark correction method. Using median as fallback.")
        master_dark = np.median(dark_data_arrays, axis=0)

    # Use configuration values to set header keywords.
    image_type_keyword = config["HEADER_SPECIFICATION"].get("image_type_keyword", "IMAGETYP")
    # NEW: Optionally get a dark label from config.ini; default to "MASTER_DARK"
    master_dark_label = config["HEADER_SPECIFICATION"].get("dark_label", "MASTER_DARK")

    hdu = fits.PrimaryHDU(data=master_dark)
    hdu.header[image_type_keyword] = master_dark_label
    hdu.header["MD_COMB"] = method  # Record the combination method.

    hdu.writeto(output_filename, overwrite=True)
    return output_filename


# ---------------------------------------------------------------------------
# Main block: Parse arguments and call make_master_dark.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create a master dark frame from a list of dark FITS files using local config.ini settings."
    )
    # OLD: parser.add_argument("--config", required=True, help="\
    # Path to the config.ini file with calibration settings")
    # NEW: Config is automatically loaded from the script directory.
    # OLD: parser.add_argument("paths", nargs="+", help="List of dark \
    # FITS files or directories to search for dark frames")
    # NEW: Use -l/--list to supply a text file listing dark FITS file paths (one per line)
    parser.add_argument("-l", "--list", required=True,
                        help="Path to a text file listing dark FITS files (one per line)")
    parser.add_argument("-o", "--output", required=True,
                        help="Path for the output master dark FITS file")
    # Optional: Override dark correction method if desired.
    parser.add_argument("-m", "--method", help="Optional override for dark correction method")
    parser.add_argument("-v", "--verbose", action="store_true", help="increase output verbosity")
    parser.add_argument("-p", "--png", action="store_true", help="prepare PNG file of created master dark")
    args = parser.parse_args()

    # NEW: Automatically load config.ini from the same directory as this script.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.ini")
    config = getconfig.load_config(config_path)

    # NEW: Override dark correction method if provided via command line.
    if args.method:
        config["IMAGE_PROCESSING"]["dark_correction_method"] = args.method

    # Load file list from the provided text file.
    with open(args.list, "r") as f:
        file_paths = [line.strip() for line in f if line.strip()]

    # NEW: Use find_dark_frames to filter dark files from the list.
    dark_files = find_dark_frames(file_paths, config)

    if not dark_files:
        print("No dark frames found matching the pattern specified in config.")
    else:
        master_dark_file = make_master_dark(dark_files, args.output, config)
        if master_dark_file:
            print(f"Master dark created: {master_dark_file}")
            
### END
