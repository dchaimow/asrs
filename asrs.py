#! /usr/bin/env python3
import numpy as np
import sys
from scipy.spatial.transform import Rotation
import nibabel as nb
from nipype.interfaces.dcm2nii import Dcm2niix
from nipype.interfaces.fsl import FLIRT, ConvertXFM, FSLCommand, ExtractROI
import logging

def qform2SiemensProtocol(qform,dims):
    # qform = DS2NS * dLPH * R * IO * NV2DV
    #
    # DS2NS: DICOM Scanner coordinates (LPH) to NIFTI Scanner Coordinates (RAS)
    # R:     Rotation in DICOM Scanner space (1st, 2nd and PE orientation)
    # IO:    Initial orientation. DICOM voxel indices to scanner
    #        coordinates of one of three standard orientations
    #        (also depends on PE Orientation!)
    #        IO = [transversal/coronal/sagittal]  * dVoxel * centerSlab
    # NV2DV: NIFTI voxel indices to DICOM voxel indices
    qform = np.matrix(qform)
    # calculate voxel dimensions
    dI, dJ, dK = np.sqrt(np.diag(np.matmul(qform.T,qform)))[:3]
    nI, nJ, nK = dims
    NV2DV = np.concatenate((np.diag([1,-1,1,1])[:,:3],
                            np.matrix([0, nJ-1, 0, 1]).T),axis=1)
    DS2NS = np.matrix(np.diag([-1,-1,1,1]))    
    dVoxel = np.matrix(np.diag([dI,dJ,dK,1]))
    centerSlab =  np.concatenate((np.eye(4)[:,:3],
                                  np.matrix([-nI/2, -nJ/2, -(nK/2-0.5), 1]).T),axis=1)
    # assuming "std" pe direction, define initial orientation transforms
    transversal = np.matrix(np.diag([1,1,1,1]))
    coronal = np.matrix(
        [[   1,   0,   0,   0 ],
         [   0,   0,   1,   0 ],
         [   0,  -1,   0,   0 ],
         [   0,   0,   0,   1 ]])
    sagittal = np.matrix(
        [[   0,   0,   1,   0 ],
         [   1,   0,   0,   0 ],
         [   0,  -1,   0,   0 ],
         [   0,   0,   0,   1 ]])
    # define orientation types:
    # orientation = rotOrder, peEstRotOrder, rotStr1, rotStr2, initialOrientation, PE, negAngleIdx
    orientations = [['XYZ',   '','T>C','>S',transversal, 1],
                    ['YXZ','XYZ','T>S','>C',transversal, 0],
                    ['ZXY',   '','C>S','>T',coronal,     1],
                    ['XZY','ZXY','C>T','>S',coronal,     0],
                    ['ZYX',   '','S>C','>T',sagittal,    1],
                    ['YZX','ZYX','S>T','>C',sagittal,    0]]
    # for each possible orientation type estimate parameters:
    for rotOrder, peEstRotOrder, rot1Str, rot2Str, initialOrientation, negAngleIdx in orientations:
        IO = initialOrientation * dVoxel * centerSlab
        dLPH_R = DS2NS.I * qform * NV2DV.I * IO.I
        dX, dY, dZ =  dLPH_R.T.round(1).tolist()[3][:3]
        R = dLPH_R[:3,:3]
        rot = Rotation.from_matrix(R)
        r1, r2, r3 = rot.as_euler(rotOrder,degrees=True).round(1)
        # Here a bit of magic happens, I estimate the 1st two rotations assuming a different rotation sequence
        # then for estimating the PE angle, but only for every 2nd orientation type
        # It seems to work, but at the moment I cannot explain why, I believe it has to do with the
        # orientation transformations being a mix of intrinsic and extrinsic rotations
        if any(peEstRotOrder):            
            _, _, r3 = rot.as_euler(peEstRotOrder,degrees=True).round(1)
        # Some estimated angles need to be negated, again not sure why, seems to depend on whether
        # orientation sequences are even or odd
        if negAngleIdx==0: r1= -r1
        if negAngleIdx==1: r2= -r2
        r3 = -r3
        # different "jumps" in PE orientation result in the same image position,
        # only changing how it is acquired (e.g. A>>P, R>>L, P>>A, ...)
        r3Alternatives = (np.mod(r3 + np.array([0, 90, -90, 180]) + 180, 360) -180).round(1)
        xStr = 'L' if dX>=0 else 'R'
        yStr = 'P' if dY>=0 else 'A'
        zStr = 'H' if dZ>=0 else 'F'
        if abs(r1)<=45 and abs(r2)<=abs(r1):
            print(f"{xStr}{abs(dX)} {yStr}{abs(dY)} {zStr}{abs(dZ)} " +
                  f"{rot1Str} {r1} {rot2Str} {r2}; possible PE orientations: {*r3Alternatives,}")

def loadFromDicomExport(dicomExportPath, seriesNumber):
    logging.getLogger('nipype.interface').setLevel(0)
    converter = Dcm2niix(source_dir=dicomExportPath, compress='n', args="-n " + str(seriesNumber))
    converter_results = converter.run()
    return converter_results.outputs.converted_files

def registerOldSlabToNewRef(slab1,ref1,ref2):
    FSLCommand.set_default_output_type('NIFTI')
    extractVolume_result = ExtractROI(in_file=slab1, t_min=0, t_size=1).run()
    slab1 = extractVolume_result.outputs.roi_file
    ref1_to_slab1_result = FLIRT(in_file=ref1, reference=slab1, out_file='ref1_in_slab1.nii',
                                 uses_qform=True, apply_xfm=True, out_matrix_file="ref1_to_slab1.txt").run()
    ref1_to_ref2_result = FLIRT(in_file=ref1, reference=ref2, out_file='ref1_in_ref2.nii', 
                                out_matrix_file="ref1_to_ref2.txt", cost_func='corratio', dof=6).run()
    invert_ref1_to_slab1_result = ConvertXFM(in_file=ref1_to_slab1_result.outputs.out_matrix_file,
                                             out_file='slab1_to_ref1.txt',
                                             invert_xfm=True).run()
    concat_slab1_to_ref1_to_ref2_result = ConvertXFM(in_file=invert_ref1_to_slab1_result.outputs.out_file,
                                                     in_file2=ref1_to_ref2_result.outputs.out_matrix_file,
                                                     out_file="slab1_to_ref2_init.txt",
                                                     concat_xfm=True).run()
    ref1_slab_to_ref2_result = FLIRT(in_file=ref1_to_slab1_result.outputs.out_file,
                                     reference=ref2,out_file='ref1_slab_in_ref2.nii',
                                     in_matrix_file=concat_slab1_to_ref1_to_ref2_result.outputs.out_file,
                                     out_matrix_file="slab1_to_ref2.txt",
                                     cost_func='corratio',dof=6, no_search=True).run()    
    xform = np.matrix(np.loadtxt(ref1_slab_to_ref2_result.outputs.out_matrix_file))
    return xform

def voxelToFsl(img):
    dI, dJ, dK = img.header.get_zooms()[:3]
    nI, _, _ = img.shape[:3]
    M = np.matrix(np.diag([dI,dJ,dK,1]))
    if np.linalg.det(img.affine)>0:
        M[0,0] = -dI
        M[0,3] = dI * (nI - 1)
    return M

def flirtToSform(xform,srcImg,refImg):
    return refImg.affine * voxelToFsl(refImg).I * xform * voxelToFsl(srcImg)

def test_qform2SiemensProtocol(nifti_fname):
    img = nb.load(nifti_fname)
    qform = img.affine
    dims = img.shape[:3]
    qform2SiemensProtocol(qform,dims)

def asrs(slab1, ref1, ref2):
    xform = registerOldSlabToNewRef(slab1,ref1,ref2)
    img_slab1 = nb.load(slab1)
    img_ref2 = nb.load(ref2)
    dims=img_slab1.shape[:3]
    sform = flirtToSform(xform,img_slab1,img_ref2) 
    qform2SiemensProtocol(sform,dims)
    
if __name__ == "__main__":
    if len(sys.argv)==2:
        test_qform2SiemensProtocol(sys.argv[1])
    else:
        dicomExportPath = sys.argv[1]
        seriesNumber = sys.argv[2]
        if len(sys.argv)==5:
            ref1 = sys.argv[3]
            slab1 = sys.argv[4]
        else:
            ref1 = 'ref1.nii'
            slab1 = 'slab1.nii'
        ref2 = loadFromDicomExport(dicomExportPath, seriesNumber)
        asrs(slab1, ref1, ref2)
