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
def find_dark_frames(paths):
    # NEW: Retrieve the dark frame pattern from config.ini (e.g., "dark")
    pattern = full_config["HEADER_SPECIFICATION"].get("dark_label", "DARK").strip().upper()
    ## print(pattern), exit
    ## print(paths), exit()
    dark_files = []
    
    for file in paths:
        try:
            with fits.open(file) as hdul:
                header = hdul[0].header
                # OLD: imagetyp = header.get("IMAGETYP", "").strip().upper()  # Check FITS type from header
                # NEW: Still read the image type from header (for backward compatibility)
                imagetyp = header.get("IMAGETYP", "").strip().upper()
                # Compare header value to the expected bias type read from config.ini
                if imagetyp == pattern:
                    dark_files.append(file)
        except Exception as e:
            print(f"Skipping {file}: {e}")
    ## print(dark_files), exit()
    return sorted(dark_files)


# ---------------------------------------------------------------------------
# Function: make_master_dark
# Description:
#   Creates a master dark frame from multiple dark frames.
#   Reads dark correction settings from config.ini.
# ---------------------------------------------------------------------------
def make_master_dark(dark_files, output_filename):
    # NEW: Check if dark correction is enabled in config.ini.
    dark_correction_enabled = full_config["IMAGE_PROCESSING"]['dark_correction']
    ## print(type(dark_correction_enabled)), exit()
    
    if not dark_correction_enabled:
        print("Dark correction is disabled in config; skipping master dark generation.")
        return None

    exptime_keyword = full_config["HEADER_SPECIFICATION"]['exposure_keyword']
    # NEW: Retrieve the dark correction method from config.ini.
    method = full_config["IMAGE_PROCESSING"]['dark_correction_method']
    ## print(method), exit()
    
    # Read all dark frame data.
    dark_data_arrays = []
    dark_data_exptimes = []
    
    for file in dark_files:
        with fits.open(file) as hdul:
            data = hdul[0].data.astype(np.float32)
            dark_data_arrays.append(data)
            dark_data_exptimes.append(float(hdul[0].header[exptime_keyword]))
    ## print(dark_data_arrays, dark_data_exptimes), exit()        

    # Combine dark frames based on the specified method.
    # (I): scaled exposure method - creating an median/average masterdark file
    #      which contains a dark signal for a one second exposure
    if method == "ScaledExposureMedian":
        print("Applying scaled exposure (median) method for dark combination.")
        dark_data_out = [arr / val for arr, val in zip(dark_data_arrays, dark_data_exptimes)]
        master_dark = np.median(dark_data_out, axis=0)
    elif method == "ScaledExposureAverage":    
        print("Applying scaled exposure (median) method for dark combination.")
        dark_data_out = [arr / val for arr, val in zip(dark_data_arrays, dark_data_exptimes)]
        master_dark = np.average(dark_data_out, axis=0)
    ## (TO DO): elif method == "EqualExposure":
    else:
        # OLD: print("Error: Unsupported dark correction method.")
        # NEW: Use median as a fallback if unsupported method encountered.
        print("Error: Unsupported dark correction method. Using median as fallback.")

    ## print(master_dark), exit()
    masterdark_filename = "masterdark.fits"
    hdu = fits.PrimaryHDU(master_dark.astype(np.float32))
    masterbias_path_to_save = working_dir + "/" + masterdark_filename

    ## hdu.header[image_type_keyword] = "" # master_dark_label
    hdu.header["MD_COMB"] = method  # Record the combination method.

    hdu.writeto(masterbias_path_to_save, overwrite=True)
    
    if args.verbose:
        print(f"[INFO]: Master bias saved as '{masterbias_path_to_save}' successfully.")

    if args.png:
        make_png(masterdark_filename)
    ## exit()
    return masterbias_path_to_save

   
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
    parser.add_argument("-c", "--config", type=str, help="Specify path to config file")
    args = parser.parse_args()
    if args.config:
        config_file = str(args.config).strip() 
    else:
        config_file = "config.ini"

    if args.verbose:
        print("[INFO] Verbosity is ON.")
    
    '''
    Reading configuration
    '''
    from calib_config import CalibConfig
    cfg = CalibConfig(config_file)
    full_config = cfg.config
    working_dir = cfg.get("DATA_STRUCTURE", "working_dir")
    results_dir = cfg.get("DATA_STRUCTURE", "results_dir")
    results_aux_dir = cfg.get("DATA_STRUCTURE", "results_aux_dir")
    
    '''
    Applying procedures
    '''
    # Load file list from the provided text file.
    with open(args.list, "r") as f:
        file_paths = [line.strip() for line in f if line.strip()]
        
    # NEW: Use find_dark_frames to filter dark files from the list.
    dark_files = find_dark_frames(file_paths)
    
    if not dark_files:
        print("No dark frames found matching the pattern specified in config.")
    else:
        master_dark_file = make_master_dark(dark_files, args.output)
    ## exit()
        if master_dark_file:
            print(f"Master dark created: '{master_dark_file}'.")

    ## TO DO:
    ## NEW: Override dark correction method if provided via command line.
    ## if args.method:
    ##    config["IMAGE_PROCESSING"]["dark_correction_method"] = args.method

    sys.exit(0)
    
### END
