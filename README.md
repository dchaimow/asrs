# asrs
Automatic Slab Repositioning System

Python code that can be used to position an fMRI slab on Siemens scanners such that it resembles a slab acquired in a previous session of the same subject. The new position is found by:

1. Registering a reference scan from the previous session the the same type of reference scan from the current session
2. Fine-tuning that registration on the volume of the slab 
3. Converting the resulting qform (mapping from voxel to scanner space) to Siemens protocol parameters

## Usage:

### Interactive GUI Mode (Simplified):

`asrs_gui.py dicomExportPath`

Simplified workflow for the common use case where you have:
- `ref1.nii` and `slab1.nii` from session 1 in the current directory
- A DICOM realtime export folder containing the reference scan from session 2

The script will present an interactive menu to select the reference series from the DICOM export, then automatically compute the new slab positioning.

### Command Line Mode:

`asrs.py dicomPath seriesNumber [ref1.nii slab1.nii]`

Finds the slab parameters based on a current Reference scan located inside dicomPath with series number seriesNumber and previously acquired reference scan ref1.nii and slab slab1.nii. If not provided, ref1.nii and slab1.nii from the current directory will be used.

`asrs.py scan.nii`

Calculates the Siemens protocol positioning parameters for the data in scan.nii

For MP2RAGE:

`asrs_mp2rage.py dicomExportPath seriesNumberINV2 seriesNumberUNI inv2_ses1.nii uni_ses1.nii slab1.nii`

or:

`asrs_mp2rage.py dicomExportPathINV2 seriesNumberINV2 dicomExportPathUNI seriesNumberUNI inv2_ses1.nii uni_ses1.nii slab1.nii`

will run the registration on the UNI images masked using a brainmask computed on the INV2 images.

## Requirements:
- nipype
- nibabel
- scipy
- numpy
- dcm2niix
- fsl

(will run in gfae container without further requirements)