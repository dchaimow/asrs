import asrs
from nipype.interfaces.fsl import BET, ImageMaths, FSLCommand
import sys

def generate_mp2rage_refs(inv2_ses1, uni_ses1,inv2_ses2, uni_ses2):
    FSLCommand.set_default_output_type('NIFTI')

    # bet on inv:
    bet1_result = BET(in_file=inv2_ses1).run()
    bet2_result = BET(in_file=inv2_ses2).run()

    # mask uni:
    maskuni1_result = ImageMaths(in_file=uni_ses1,mask_file=bet1_result.outputs.out_file).run()
    maskuni2_result = ImageMaths(in_file=uni_ses2,mask_file=bet2_result.outputs.out_file).run()

    ref1=maskuni1_result.outputs.out_file
    ref2=maskuni2_result.outputs.out_file
    return ref1, ref2

if __name__ == "__main__":
    if len(sys.argv)==7:
        dicomExportPath = sys.argv[1]
        seriesNumberINV2 = sys.argv[2]
        seriesNumberUNI = sys.argv[3]
        inv2_ses1 = sys.argv[4]    
        uni_ses1 = sys.argv[5]
        slab1 = sys.argv[6]
        inv2_ses2 = asrs.loadFromDicomExport(dicomExportPath, seriesNumberINV2)
        uni_ses2 = asrs.loadFromDicomExport(dicomExportPath, seriesNumberUNI)
    elif len(sys.argv)==8:
        dicomExportPathINV2 = sys.argv[1]
        seriesNumberINV2 = sys.argv[2]
        dicomExportPathUNI = sys.argv[3]
        seriesNumberUNI = sys.argv[4]
        inv2_ses1 = sys.argv[5]    
        uni_ses1 = sys.argv[6]
        slab1 = sys.argv[7]
        inv2_ses2 = asrs.loadFromDicomExport(dicomExportPathINV2, seriesNumberINV2)
        uni_ses2 = asrs.loadFromDicomExport(dicomExportPathUNI, seriesNumberUNI)
    else:
        print('Usage: asrs_mp2rage.py dicomExportPath seriesNumberINV2 seriesNumberUNI inv2_ses1 uni_ses1 slab1')
        print('or: asrs_mp2rage.py dicomExportPathINV2 seriesNumberINV2 dicomExportPathUNI seriesNumberUNI inv2_ses1 uni_ses1 slab1')
        exit
    ref1, ref2 = generate_mp2rage_refs(inv2_ses1, uni_ses1,inv2_ses2, uni_ses2)
    asrs.asrs(slab1, ref1, ref2)
