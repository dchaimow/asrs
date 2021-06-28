# asrs
Automatic Slab Repositioning System

Python code that can be used to position an fMRI slab on Siemens scanners such that it resembles a slab acquired in a previous session of the same subject. The new position is found by:

1. Registering a reference scan from the previous session the the same type of reference scan from the current session
2. Fine-tuning that registration on the volume of the slab 
3. Converting the resulting qform (mapping from voxel to scanner space) to Siemens protocol parameters
