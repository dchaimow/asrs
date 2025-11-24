#!/usr/bin/env python3
import asrs
import sys
import os
from dicom_series_selector import dicom_series_selector
""" This script handles one specific use case of ASRS, it assume that:
- there are two locally available nifti files from sessions 1: ref1.nii and slab1.nii
- there is a dicom realtime export folder in which at some point the dicoms belonging to
  the reference images of session 2 will be available
- once they are available, the user can select the series interactively and asrs will compute
  the new slab positioning accordingly

Usage: asrs_mp2rage.py dicomExportPath 
"""
if __name__ == "__main__":
    # we check if all requirements are met
    # 1. check if asrs_gui was started with exactly one argument that is an existing folder
    if len(sys.argv)!=2:
        print("Usage: asrs_mp2rage.py dicomExportPath")
        sys.exit(1)
    dicomExportPath = sys.argv[1]
    if not os.path.exists(dicomExportPath) or not os.path.isdir(dicomExportPath):
        print("Error: dicomExportPath does not exist or is not a folder")
        sys.exit(1)
    # 2. Check if slab1.nii exist (and there is no additional slab1.nii.gz)
    if not os.path.exists("slab1.nii"):
        print("Error: slab1.nii not found in current folder")
        sys.exit(1)
    if os.path.exists("slab1.nii.gz"):
        print("Error: slab1.nii.gz (in addition to slab1.nii) found in current folder, please delete")
        sys.exit(1)

    slab1 = 'slab1.nii'

    # 3. Check if ref1.nii exist (and there is no additional ref1.nii.gz)
    if not os.path.exists("ref1.nii"):
        print("Error: ref1.nii not found in current folder")
        sys.exit(1)
    if os.path.exists("ref1.nii.gz"):
        print("Error: ref1.nii.gz (in addition to ref1.nii) found in current folder, please delete")
        sys.exit(1)

    ref1 = 'ref1.nii'

    # if all requirements are met, we can start the selection GUI 
    crc_series_number = dicom_series_selector(dicomExportPath, menu_type="interactive")
    ref2 = asrs.loadFromDicomExport(dicomExportPath, crc_series_number)
    print("Running ASRS...")
    asrs.asrs(slab1, ref1, ref2)
