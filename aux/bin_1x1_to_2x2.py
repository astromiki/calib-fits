import os
import numpy as np
from astropy.io import fits
import glob

def bin_2x2(data):
    # Simple 2x2 binning (assuming shape is divisible by 2)
    return data.reshape(data.shape[0]//2, 2, data.shape[1]//2, 2).mean(axis=(1,3))

def process_fits_file(input_path, output_path):
    with fits.open(input_path) as hdul:
        data = hdul[0].data
        header = hdul[0].header

        if data.shape != (4096, 4096):
            raise ValueError(f"{input_path} does not have shape 4096x4096, found {data.shape}")

        binned_data = bin_2x2(data)

        # Update header to reflect new dimensions
        header['NAXIS1'] = binned_data.shape[1]
        header['NAXIS2'] = binned_data.shape[0]

        fits.writeto(output_path, binned_data, header, overwrite=True)

def batch_bin_fits(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    fits_files = glob.glob(os.path.join(input_dir, "*.fits"))

    for file in fits_files:
        filename = os.path.basename(file)
        output_path = os.path.join(output_dir, filename)
        process_fits_file(file, output_path)
        print(f"Binned and saved: {output_path}")

if __name__ == "__main__":
    input_folder = "./input_fits"
    output_folder = "./binned_fits"
    batch_bin_fits(input_folder, output_folder)

