#!/usr/bin/env python3

# This script requires only two things:
# 1 - list of files to be corrected
# 2- masterbias file

# =============================================================================
# Filename: dark_correction.py
# Description:
#   This script applies a previously generated master dark to images.
#   It reads in the raw frame and subtracts the master dark from each pixel,
#   removing the electronic offset. Master dark is scaled by the exposure time
#   of the scientific images.
# =============================================================================


import sys
import numpy as np
from astropy.io import fits
from pathlib import Path
import getconfig
import warnings
warnings.filterwarnings("ignore")


def apply_dark_correction(list_in, list_out, md):
    # Applies bias correction to all non-bias FITS frames in the directory
    #path = Path(directory)
    md_data = fits.open(md, mode="readonly")[0].data.astype(np.float32)
    ## print(mb_data), exit()
    type_keyword = cfg.get("HEADER_SPECIFICATION", "image_type_keyword")
    ## expected_bias = full_config["HEADER_SPECIFICATION"].get("dark_label", "DARK").strip().upper()
    files_out = []
    exptime_keyword = full_config["HEADER_SPECIFICATION"]['exposure_keyword']
    ## exit()

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
                # skipping darks & biases 
                # TO DO:
                # - incorporate evaluation module here
                if imagetyp == "BIAS" or imagetyp == "DARK":
                    continue

                # Read image data and apply bias correction
                data = hdul[0].data.astype(np.float32)
                exposure = float(header[exptime_keyword])
                ## print(imagetyp, exposure)
                
                corrected_data = data - exposure * md_data  # dark subtraction HERE
                ## print(corrected_data), exit()
                extention = str(file.split(".")[-1])
                new_filepath = str(file.replace("-b","").split("."+extention)[0]) + "-bd." + extention
                ## print(new_filepath), exit()                
                ## print(file, new_filepath)
                ## continue  
                # Save the bias-corrected image
                hdu = fits.PrimaryHDU(corrected_data.astype(np.float32), header=header)
                
                ## TO DO: add header entries
                hdu.writeto(new_filepath, overwrite=True)
                hdul.flush()
                if verbose:
                    print(f"Dark-subtracted file saved: {new_filepath}")
                files_out.append(new_filepath)
                
        except Exception as e:
            print(f"Skipping {file}: {e}")

        with open(list_out, "w", encoding="utf-8") as f:
            for item in files_out:
                ## print(item)
                f.write(item + "\n")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python dark_correction.py <list_of_input_files> \n \
        <list_of_output_files> <path_to_masterbias_file> <path_to_config_file>")
        sys.exit(1)
    ## print(sys.argv), exit()

    verbose = False
    list_of_files_in    = sys.argv[1]
    list_of_files_out   = sys.argv[2]
    masterdark_file     = sys.argv[3]
    config_file         = sys.argv[4]
    ## print(verbose, list_of_files_in, list_of_files_out, masterdark_file, config_file)
    ## exit()
    
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
    apply_dark_correction(list_of_files_in, list_of_files_out, masterdark_file)
    sys.exit(0)
    
### END
