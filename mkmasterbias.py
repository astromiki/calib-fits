#!/usr/bin/env python3

# =============================================================================
# Filename: mkmasterbias.py
# Description:
#   This script takes several raw bias frames and merges them into one master
#   bias. By combining multiple bias frames, it helps minimize random noise
#   in the final master bias. We need it to remove the electronic offset from
#   exposures, ensuring more precise data calibration.
#
#   This version uses config.ini values rather than the FITS header
#   for image type or other calibration parameters.
#   - param bias_files: List of paths to FITS files known to be bias frames.
#   - param output_filename: Where to write the resulting master bias.
#   - param config: A ConfigParser or dictionary-like object holding calibration settings.
#   - return: The path to the newly created master bias file.
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
# Function: find_bias_frames
# Description:
#   OLD: Reads the "IMAGETYP" value directly from the header.
#   NEW: Reads the expected bias label from config.ini and compares the header's
#        "IMAGETYP" value to that expected value.
# ---------------------------------------------------------------------------
def find_bias_frames(flist):
    # NEW: Read the expected bias type from config.ini (e.g., "BIAS" or user-defined)
    ##working_dir = config.get("HEADER_SPECIFICATION", "working_dir")
    expected_bias = full_config["HEADER_SPECIFICATION"].get("bias_label", "BIAS").strip().upper()
    bias_files = []
    # OLD: for file in flist:  # Search for all FITS files and check header for IMAGETYP
    for file in flist:
        try:
            with fits.open(file) as hdul:
                header = hdul[0].header
                # OLD: imagetyp = header.get("IMAGETYP", "").strip().upper()  # Check FITS type from header
                # NEW: Still read the image type from header (for backward compatibility)
                imagetyp = header.get("IMAGETYP", "").strip().upper()
                # Compare header value to the expected bias type read from config.ini
                if imagetyp == expected_bias:
                    bias_files.append(file)
        except Exception as e:
            print(f"Skipping {file}: {e}")
    return sorted(bias_files)


# ---------------------------------------------------------------------------
# Function: create_master_bias
# Description:
#   Creates a master bias frame from multiple bias frames.
#   Combination method (sigma-clipping, etc.) and calibration parameters
#   are now read from config.ini.
# ---------------------------------------------------------------------------
def create_master_bias(flist):
    # (old):
    #if config is None:
    #    print("[ERROR]: Could not load configuration. Exiting.")
    #    sys.exit(1)

    # Establish calibration parameters from config.ini:
    bias_subtraction = cfg.get("IMAGE_PROCESSING", "bias_subtraction")
    method = cfg.get("IMAGE_PROCESSING", "bias_subtraction_method")
    sigma = cfg.get("IMAGE_PROCESSING", "bias_subtraction_sigma")
    working_dir = cfg.get("DATA_STRUCTURE", "working_dir")
    ## print(bias_subtraction, method, sigma, working_dir), exit()

    if bias_subtraction is False:
        print("Bias subtraction is disabled in config. Exiting.")
        sys.exit(0)

    # ---------------------------------------------------------------------------
    # NEW: Use find_bias_frames with config object to determine bias files.
    # ---------------------------------------------------------------------------
    bias_files = find_bias_frames(flist)

    if len(bias_files) == 0:
        print("Error: No bias frames found for creating a master bias frame.")
        sys.exit(1)
    else:
        if args.verbose:
            print(f"[INFO] Found {len(bias_files)} bias frames. Processing...")

    # Read all bias images into a list
    bias_data = []
    for file in bias_files:
        with fits.open(file) as hdul:
            data = hdul[0].data.astype(np.int16)  # Convert to int16
            bias_data.append(data)

    # Stack into a 3D numpy array
    bias_stack = np.array(bias_data)

    # Apply median sigma-clipped combination
    if method == "MedianSigmaClipped":
        if args.verbose:
            print(f"[>>>>] Applying sigma-clipped median with sigma = {sigma}...")
        clipped_bias = sigma_clip(bias_stack, sigma=sigma, axis=0)
        master_bias = np.nanmedian(clipped_bias, axis=0)
    else:
        print("[ERROR]: Unsupported bias subtraction method.")
        sys.exit(1)

    # ---------------------------------------------------------------------------
    # OLD: Create "master_bias" file using hardcoded header keywords.
    # NEW: Use configuration values from config.ini to set header keywords.
    # ---------------------------------------------------------------------------
    hdu = fits.PrimaryHDU(master_bias.astype(np.float32))
    # OLD: hdu.header['MYFIELD'] = ('MyValue', 'Description of my new field')
    # NEW: Set a custom field from config.ini if available; default to "MyValue"
    
    ### TO DO:
    # - add custom comments in this section
    
    ##hdu.header['MYFIELD'] = full_config["HEADER_SPECIFICATION"].get("custom_field", "MyValue")
    ##hdu.header['COMMENT'] = ('aaa', 'Sample comment')
    ## print(working_dir + masterbias_filename), exit()
    
    
    masterbias_path_to_save = working_dir + "/" + masterbias_filename
    hdu.writeto(masterbias_path_to_save, overwrite=True)

    if args.verbose:
        print(f"[INFO]: Master bias saved as '{masterbias_path_to_save}' successfully.")

    if args.png:
        make_png(masterbias_filename)


# ---------------------------------------------------------------------------
# Function: make_png
# Description:
#   Creates a PNG image of the master bias file using zscale for display.
# ---------------------------------------------------------------------------
def make_png(ffile):
    ofile = str(ffile).split("." + str(ffile).split(".")[-1])[0] + ".png"
    with fits.open(ffile) as hdul:
        data = hdul[0].data
    interval = ZScaleInterval()
    vmin, vmax = interval.get_limits(data)
    plt.imshow(data, origin='lower', vmin=vmin, vmax=vmax, cmap='gray')
    plt.colorbar(label='Pixel Value (zscale)')
    plt.title('MasterBias file')
    plt.savefig(ofile, dpi=300, bbox_inches='tight')
    plt.close()
    if args.verbose:
        print("[INFO] Created PNG file: ", ofile)


# ---------------------------------------------------------------------------
# Helper: get_list_of_files_from_file
# Description:
#   Reads a text file listing file paths (one per line) and returns a list.
# ---------------------------------------------------------------------------
def get_list_of_files_from_file(fname):
    with open(fname, "r") as file:
        file_list = [line.strip() for line in file]
    return file_list


# ---------------------------------------------------------------------------
# Main block: Parse arguments and call create_master_bias.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Define and parse arguments
    parser = argparse.ArgumentParser(description="Create master bias frames for a given list of files.")
    parser.add_argument("-l", "--list", type=str,
                        help="List of bias frames to be combined (text file with one file per line)", required=True)
    parser.add_argument("-d", "--dir", type=str,
                        help="Look for files in specified directory and combine biases")
    parser.add_argument("-m", "--method", type=str, help="Override bias subtraction method")
    parser.add_argument("-s", "--sigma", type=float,
                        help="Sigma-clipping value for outlier rejection (default: 2.5).")
    parser.add_argument("-o", "--output", type=str, default="masterbias.fits",
                        help="Default name of the output master bias file.")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Increase output verbosity")
    parser.add_argument("-p", "--png", action="store_true",
                        help="Prepare PNG file of created master bias file")
    parser.add_argument("-c", "--config", type=str, help="Specify path to config file")

    args = parser.parse_args()
    arg_sigma = args.sigma
    if args.config:
        config_file = str(args.config).strip() 
    else:
        config_file = "config.ini"

    if args.verbose:
        print("[INFO] Verbosity is ON.")
        print("[INFO] Used SIGMA for sigma-clipping: ", arg_sigma)

    '''
    Reading configuration
    '''
    from calib_config import CalibConfig
    cfg = CalibConfig(config_file)
    full_config = cfg.config
    ## print(full_config), exit()

    ## obs_name = cfg.get("GENERAL", "observatory_name")
    ## gain = cfg.get("DEFAULT_VALUES", "gain")
    ## print(f"Observatory: {obs_name}, Gain: {gain}")
    working_dir = cfg.get("DATA_STRUCTURE", "working_dir")
    results_dir = cfg.get("DATA_STRUCTURE", "results_dir")
    results_aux_dir = cfg.get("DATA_STRUCTURE", "results_aux_dir")
    
    '''
    Applying procedures
    '''
    masterbias_filename = str(args.output)
    list_of_bias_frames = args.list
    file_list = get_list_of_files_from_file(list_of_bias_frames)
    ## print(file_list), exit()
    create_master_bias(file_list)
    ## print(working_dir, results_dir, results_aux_dir, masterbias_filename)

    sys.exit(0) 
    
### END
