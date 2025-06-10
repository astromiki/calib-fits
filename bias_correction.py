#!/usr/bin/env python3

# This script requires only two things:
# 1 - list of files to be corrected
# 2- masterbias file

# =============================================================================
# Filename: biascorrection.py
# Description:
#   This script applies a previously generated master bias to raw images.
#   It reads in the raw frame and subtracts the master bias from each pixel,
#   removing the electronic offset. We need it as a crucial preprocessing step
#   for astronomical data before dark subtraction or flat-field correction.
# =============================================================================


import sys
import numpy as np
from astropy.io import fits
from pathlib import Path
import getconfig
## import mkmasterbias  # Import master bias creation
import warnings
warnings.filterwarnings("ignore")


def apply_bias_correction(list_in, list_out, mb):
    # Applies bias correction to all non-bias FITS frames in the directory
    #path = Path(directory)
    mb_data = fits.open(mb, mode="readonly")[0].data.astype(np.float32)
    ## print(mb_data), exit()
    type_keyword = cfg.get("HEADER_SPECIFICATION", "image_type_keyword")
    expected_bias = full_config["HEADER_SPECIFICATION"].get("bias_label", "BIAS").strip().upper()
    files_out = []

    with open(list_in) as f:
        files_in = f.read().splitlines()
    ## print(files), exit()        

    for file in files_in:
        try:
            ## print(file)
            ## continue
            with fits.open(file, mode="readonly") as hdul:
                header = hdul[0].header
                ## print(header)
                ## continue
                imagetyp = header[type_keyword].strip().upper()  # Check FITS type
                if imagetyp == expected_bias:
                    continue
                ## else:
                ##    print(file)

                # Read image data and apply bias correction
                data = hdul[0].data.astype(np.float32)
                corrected_data = data - mb_data  # Bias subtraction
                ## print(corrected_data), exit()
                extention = str(file.split(".")[-1])
                new_filepath = str(file.split("."+extention)[0]) + "-b." + extention
                ##print(new_filepath), exit()

                # Save the bias-corrected image
                hdu = fits.PrimaryHDU(corrected_data.astype(np.float32), header=header)
                
                ## TO DO: add header entries
                hdu.writeto(new_filepath, overwrite=True)
                hdul.flush()
                if verbose:
                    print(f"Bias-subtracted file saved: {new_filepath}")
                files_out.append(new_filepath)
                
        except Exception as e:
            print(f"Skipping {file}: {e}")

        with open(list_out, "w", encoding="utf-8") as f:
            for item in files_out:
                f.write(item + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python bias_correction.py <list_of_input_files> \n \
        <list_of_output_files> <path_to_masterbias_file> <path_to_config_file>")
        sys.exit(1)

    verbose = False
    list_of_files_in    = sys.argv[1]
    list_of_files_out   = sys.argv[2]
    masterbias_file     = sys.argv[3]
    config_file         = sys.argv[4]

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
    apply_bias_correction(list_of_files_in, list_of_files_out, masterbias_file)
    sys.exit(0)
    
### END
