# asrs
Automatic Slab Repositioning System

Python code that can be used to position an fMRI slab on Siemens scanners such that it resembles a slab acquired in a previous session of the same subject. The new position is found by:

1. Registering a reference scan from the previous session the the same type of reference scan from the current session
2. Fine-tuning that registration on the volume of the slab 
3. Converting the resulting qform (mapping from voxel to scanner space) to Siemens protocol parameters

Useage:

asrs.py dicomPath seriesNumber \[ref1.nii slab1.nii\]

Finds the slab parameters based on a current Reference scan located inside dicomPath with series number seriesNumber and previously acquired reference scan ref1.nii and slab slab1.nii. If not provided, ref1.nii and slab1.nii from the current disrectory will be used.

asrs.py scan.nii

Calculates the Siemens protocol positioning parameters for the data in scan.nii
