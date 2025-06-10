#!/usr/bin/env python3

import os
import sys

def list_fits_files(directory, output_file='fits_list.txt'):
    fits_files = sorted([
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.lower().endswith(('.fits', '.fit'))
    ])

    if not fits_files:
        print("No FITS files found in the directory.")
        return

    with open(output_file, 'w') as f:
        for file in fits_files:
            f.write(f"{file}\n")

    print(f"List saved to '{output_file}' with {len(fits_files)} FITS files.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python mkflist.py <directory>")
        sys.exit(1)

    directory = sys.argv[1]
    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a valid directory.")
        sys.exit(1)

    list_fits_files(directory)
