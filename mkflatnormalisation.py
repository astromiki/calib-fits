#!/usr/bin/env python3

import os
import sys
import numpy as np
from astropy.io import fits
from collections import defaultdict

def read_filenames(input_arg):
    if input_arg.endswith('.txt'):
        with open(input_arg, 'r') as f:
            files = [line.strip() for line in f if line.strip()]
    else:
        files = input_arg.split()
    return files

def get_filter_from_header(header):
    filt = header.get('FILTER', '').strip().upper()
    return filt if filt in ['U', 'B', 'V', 'R', 'I'] else 'UNKNOWN'

def normalize_flat(data):
    avg = np.mean(data)
    return data / avg if avg != 0 else data

def process_flats(file_list):
    filter_groups = defaultdict(list)
    shape_by_filter = {}

    for filename in file_list:
        with fits.open(filename) as hdul:
            header = hdul[0].header
            data = hdul[0].data.astype(np.float32)
            filt = get_filter_from_header(header)

            if filt == 'UNKNOWN':
                print(f"Skipping {filename}: unknown or unsupported filter.")
                continue

            if filt not in shape_by_filter:
                shape_by_filter[filt] = data.shape
            elif data.shape != shape_by_filter[filt]:
                print(f"Skipping {filename}: shape {data.shape} does not match expected {shape_by_filter[filt]} for filter {filt}")
                continue

            filter_groups[filt].append((data, header, filename))

    all_output_paths = []

    for filt, frames in filter_groups.items():
        if len(frames) < 2:
            print(f"Skipping filter '{filt}': not enough flats (only {len(frames)}).")
            continue

        base_dir = os.path.dirname(frames[0][2])
        output_dir = os.path.join(base_dir, 'normalised_flats')
        os.makedirs(output_dir, exist_ok=True)

        normalized_data = []
        headers = []

        for data, header, _ in frames:
            normalized_data.append(normalize_flat(data))
            headers.append(header)

        with np.errstate(divide='ignore', invalid='ignore'):
            for i in range(1, len(normalized_data)):
                divided = normalized_data[i] / normalized_data[i - 1]
                outname = os.path.join(output_dir, f"flat_norm_{filt}_{i}.fits")
                fits.writeto(outname, divided, headers[i], overwrite=True)
                all_output_paths.append(outname)
                print(f"Written: {outname}")

    # Write one combined list for all filters
    if all_output_paths:
        output_list_path = os.path.join(output_dir, 'normalised_fits_list.txt')
        with open(output_list_path, 'w') as f:
            for path in all_output_paths:
                f.write(path + '\n')
        print(f"Combined normalised list written to: {output_list_path}")
    else:
        print("No valid normalised flats created.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python mkflatnormalisation.py <flat_list.txt> or <file1.fits file2.fits ...>")
        sys.exit(1)

    if len(sys.argv) == 2:
        input_files = read_filenames(sys.argv[1])
    else:
        input_files = sys.argv[1:]

    process_flats(input_files)
