#!/usr/bin/env python3
"""
calib_prep_lists.py
===================

Create calibrated‑preparation file lists for FITS images.

One (and only one) of the following options must be given:
  -l <listfile>    text file containing a list of FITS filenames (one per line)
  -d <directory>   directory containing FITS files to process
  -a <archive>     .tar(.gz) | .tar.gz | .zip archive with FITS files

For every entry ``file.fits`` in the base list, the script writes six
additional lists in the current working directory, containing the filenames
modified with calibration suffixes:

  * «-b»   → bias‑corrected  (file-b.fits)
  * «-d»   → dark‑corrected  (file-d.fits)
  * «-f»   → flat‑corrected  (file-f.fits)   [intermediate]
  * «-bd»  → bias+dark       (file-bd.fits)
  * «-bf»  → bias+flat       (file-bf.fits)
  * «-df»  → dark+flat       (file-df.fits)
  * «-bdf» → bias+dark+flat  (file-bdf.fits)

(The «-f» list is implicit in «-bf»/«-df»/«-bdf», but included here for
completeness.)

The derived list filenames follow the pattern

    <base>-<suffix>.lst

where <base> is the stem of the original list name, directory name, or
archive name.

Examples
--------
::

   $ calib_prep_lists.py -l observations.lst
   # → writes observations-b.lst, observations-d.lst, ...

   $ calib_prep_lists.py -d /data/20250531
   # → writes 20250531.lst (original names) and the six derived lists

   $ calib_prep_lists.py -a night1.tar.gz
   # → unpacks to a temp dir, then writes night1.lst + derived lists

All files are written in the *current* directory; paths inside each list
preserve the original relative paths.
"""

from __future__ import annotations

import argparse
import os
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import Iterable, List

# ---- constants ------------------------------------------------------------
SUFFIXES = ["", "-b", "-d", "-bd", "-bf", "-df", "-bdf"]
FITS_EXTENSIONS = {".fits", ".fit", ".FITS", ".FIT"}

# ---- helpers --------------------------------------------------------------

def fits_files_in_directory(directory: Path) -> List[str]:
    """Return relative paths of FITS files in *directory* (non‑recursive)."""
    return sorted(
        [str(p.relative_to(directory)) for p in directory.iterdir() if p.suffix in FITS_EXTENSIONS]
    )


def modified_filename(original: str, suffix: str) -> str:
    """Return *original* with *suffix* inserted before the extension."""
    p = Path(original)
    return str(p.with_name(p.stem + suffix + p.suffix))


def read_list_file(listfile: Path) -> List[str]:
    """Read newline‑separated filenames from *listfile* (stripped, blank lines skipped)."""
    with listfile.open("r", encoding="utf‑8") as f:
        lines = [line.strip() for line in f if line.strip()]
    return lines


def write_list_file(name: str, lines: Iterable[str]) -> None:
    """Write *lines* to *name* in the current working directory."""
    with Path(name).open("w", encoding="utf‑8") as f:
        f.write("\n".join(lines) + "\n")


# ---- core workflow --------------------------------------------------------

def generate_lists(base_name: str, originals: List[str]) -> None:
    """Given *originals* (filenames) write the derivative list files."""
    # Base list (only if we created it ourselves)
    if not Path(base_name + ".lst").exists():
        write_list_file(f"{base_name}.lst", originals)

    # Derived lists
    for suffix in SUFFIXES:
        derived = [modified_filename(fn, suffix) for fn in originals]
        write_list_file(f"{base_name}{suffix}.lst", derived)


# ---- argument parsing -----------------------------------------------------

def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare calibration file lists for FITS image processing.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-l", "--list", metavar="FILE", help="existing list file with FITS names")
    group.add_argument("-d", "--directory", metavar="DIR", help="directory containing FITS files")
    group.add_argument("-a", "--archive", metavar="ARCH", help="zip, tar, or tar.gz archive")
    return parser.parse_args(argv)


# ---- main entry point -----------------------------------------------------

def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)

    if args.list:
        list_path = Path(args.list).expanduser().resolve()
        if not list_path.is_file():
            sys.exit(f"Error: list file '{list_path}' not found")
        originals = read_list_file(list_path)
        base_name = list_path.with_suffix("").name
        generate_lists(base_name, originals)

    elif args.directory:
        dir_path = Path(args.directory).expanduser().resolve()
        if not dir_path.is_dir():
            sys.exit(f"Error: directory '{dir_path}' not found")
        originals = fits_files_in_directory(dir_path)
        if not originals:
            sys.exit("Error: no FITS files found in directory")
        base_name = dir_path.name
        generate_lists(base_name, originals)

    elif args.archive:
        arc_path = Path(args.archive).expanduser().resolve()
        if not arc_path.is_file():
            sys.exit(f"Error: archive '{arc_path}' not found")
        # Create a temporary extraction directory
        with tempfile.TemporaryDirectory() as tmpdir_str:
            tmpdir = Path(tmpdir_str)
            # Unpack accordingly
            if zipfile.is_zipfile(arc_path):
                with zipfile.ZipFile(arc_path, "r") as zf:
                    zf.extractall(tmpdir)
            elif tarfile.is_tarfile(arc_path):
                with tarfile.open(arc_path, "r:*") as tf:
                    tf.extractall(tmpdir)
            else:
                sys.exit("Error: unsupported archive format")

            originals = [str(p.relative_to(tmpdir)) for p in tmpdir.rglob("*" ) if p.suffix in FITS_EXTENSIONS]
            if not originals:
                sys.exit("Error: no FITS files found inside archive")
            base_name = arc_path.stem.replace(".tar", "")  # strip .tar from .tar.gz
            generate_lists(base_name, sorted(originals))

    else:  # should never reach because of mutually exclusive group
        sys.exit("Internal argument parsing error")


if __name__ == "__main__":
    main()

