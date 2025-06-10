#!/usr/bin/env python3

# =============================================================================
# Filename: flat_correction.py
# Description:
#   This script applies a previously generated master flats to science images.
# =============================================================================

import sys
import numpy as np
from astropy.io import fits
from pathlib import Path
import getconfig
import warnings
warnings.filterwarnings("ignore")
import shutil

def get_filter_from_header(header):
    filt = header.get('FILTER', '').strip()
    ## print(filt)
    return filt if filt in ['U', 'B', 'V', 'R', 'I', 'Haw', 'Han', 'None', "-"] else 'UNKNOWN'

def apply_flat_correction(list_in, list_out):
    # Applies bias correction to all non-bias FITS frames in the directory
    #path = Path(directory)
    
    with open(list_in) as f:
        files_in = f.read().splitlines()
    ## print(files_in), exit()    
    all_filter_entries = []

    for filename in files_in:
        with fits.open(filename) as hdul:
            header = hdul[0].header
            data = hdul[0].data.astype(np.float32)
            imagetyp = header.get("IMAGETYP", "").strip().upper()
            if imagetyp == "OBJECT":
                filt = get_filter_from_header(header)
                all_filter_entries.append(filt)
    all_existing_filters = set(all_filter_entries)
    ## print(all_existing_filters), exit()
    
    # calibrating...
    for filename in files_in:
        with fits.open(filename) as hdul:
            header = hdul[0].header
            data = hdul[0].data.astype(np.float32)
            imagetyp = header.get("IMAGETYP", "").strip().upper()
            if imagetyp == "OBJECT":
                filt = get_filter_from_header(header)
                mf_file = working_dir + "/masterflat_" + filt + "_norm.fits"
                mf_data = fits.open(mf_file, mode="readonly")[0].data.astype(np.float32)
                
                data_cal = data / mf_data
                extention = str(filename.split(".")[-1])
                new_filepath = str(filename.replace("-bd","").split("."+extention)[0]) + "-bdf." + extention
     
                # Save the bias-corrected image
                hdu = fits.PrimaryHDU(data_cal.astype(np.float32), header=header)
                ## TO DO: add header entries
                hdu.writeto(new_filepath, overwrite=True)
                hdul.flush()
                
                
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python flat_correction.py <list_of_input_files> \n \
        <list_of_output_files> <path_to_config_file>")
        sys.exit(1)
    ## print(sys.argv), exit()

    verbose = False
    list_of_files_in    = sys.argv[1]
    list_of_files_out   = sys.argv[2]
    config_file         = sys.argv[3]
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
    apply_flat_correction(list_of_files_in, list_of_files_out)
    sys.exit(0)
    
### END
