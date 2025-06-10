#!/usr/bin/env python3

import os
import sys
import numpy as np
from astropy.io import fits
from collections import defaultdict
import calib_config
import shutil

def read_filenames(input_arg):
    if input_arg.endswith('.lst'):
        with open(input_arg, 'r') as f:
            files = [line.strip() for line in f if line.strip()]
    else:
        files = input_arg.split()
    return files

def get_filter_from_header(header):
    filt = header.get('FILTER', '').strip()
    ## print(filt)
    return filt if filt in ['U', 'B', 'V', 'R', 'I', 'Haw', 'Han', 'None', "-"] else 'UNKNOWN'

def normalize_flat(data):
    avg = np.mean(data)
    return data / avg if avg != 0 else data

def process_flats(file_list):
    all_filter_entries = []
    filter_groups = defaultdict(list)
    shape_by_filter = {}

    for filename in file_list:
        with fits.open(filename) as hdul:
            header = hdul[0].header
            data = hdul[0].data.astype(np.float32)
            imagetyp = header.get("IMAGETYP", "").strip().upper()
            if imagetyp != "FLAT":
                continue
            ## print(filt)
            ## continue            
            filt = get_filter_from_header(header)
            all_filter_entries.append(filt)
            if filt == 'UNKNOWN':
                print(f"Skipping {filename}: unknown or unsupported filter.")
                continue

            if filt not in shape_by_filter:
                shape_by_filter[filt] = data.shape
            elif data.shape != shape_by_filter[filt]:
                print(f"Skipping {filename}: shape {data.shape} does not match expected \
                        {shape_by_filter[filt]} for filter {filt}")
                continue
            filter_groups[filt].append((data, header, filename))

    all_output_paths = []
    all_filters = set(all_filter_entries)
    ## print(all_filters), exit()
    ## print(filter_groups["B"])
    ## exit()
    
    for filt_name in all_filters:
        ## print(filt_name)
        data_all = []
        data_all_norm = []
    
        for filename in file_list:
            with fits.open(filename) as hdul:
                header = hdul[0].header
                imagetyp = header.get("IMAGETYP", "").strip().upper()
                if imagetyp == "FLAT":
                    filt = get_filter_from_header(header)
                    if filt == filt_name:
                        ## print(filename)
                        data = hdul[0].data.astype(np.float32)
                        data_all.append(data)
                        data_all_norm.append(data / np.average(data))
                        ## print(data)
                        ## print(data / np.average(data))
                        ## exit()
        
        median_flat = np.median(data_all, axis=0)
        median_normflat = np.median(data_all_norm, axis=0)
        ## print(median_flat)
        ## print(median_normflat)
        
        flat_path_to_save = working_dir + "/" + "masterflat_" + filt_name + ".fits"
        normflat_path_to_save = working_dir + "/" + "masterflat_" + filt_name + "_norm.fits"
        
        flat_path_to_store = results_aux_dir + "/" + "masterflat_" + filt_name + ".fits"
        normflat_path_to_store = results_aux_dir + "/" + "masterflat_" + filt_name + "_norm.fits"
        
        hdu = fits.PrimaryHDU(median_flat.astype(np.float32))
        hdun = fits.PrimaryHDU(median_normflat.astype(np.float32))
        
        hdu.writeto(flat_path_to_save, overwrite=True)
        hdun.writeto(normflat_path_to_save, overwrite=True)
        
        # copy flats to results aux as well to keep it there
        shutil.copy(flat_path_to_save, flat_path_to_store)
        shutil.copy(normflat_path_to_save, normflat_path_to_store)
        
    ## if args.verbose:
    ##    print(f"[INFO]: Master bias saved as '{masterbias_path_to_save}' successfully.")
        
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python mkmasterflats.py <config_file_path> <flat_list.txt> or <file1.fits file2.fits ...>")
        sys.exit(1)

    config_file = sys.argv[1]
    '''
    Reading configuration
    '''
    from calib_config import CalibConfig
    cfg = CalibConfig(config_file)
    full_config = cfg.config
    ## print(full_config), exit()

    working_dir = cfg.get("DATA_STRUCTURE", "working_dir")
    results_dir = cfg.get("DATA_STRUCTURE", "results_dir")
    results_aux_dir = cfg.get("DATA_STRUCTURE", "results_aux_dir")
    
    '''
    Applying procedures
    '''

    if len(sys.argv) == 3:
        input_files = read_filenames(sys.argv[2])
    else:
        input_files = sys.argv[2:] 
    ## print(input_files), exit()
    
    process_flats(input_files)
    sys.exit(0)
    
### END
