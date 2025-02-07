import os, sys
from glob import glob
import tempfile
from shutil import rmtree
sys.path.insert(0,'/home/jagust/cindeem/CODE/ucsf')

import nipype.interfaces.spm as spm
from nipype.interfaces.base import CommandLine
import nipype.interfaces.matlab as mlab
from nipype.utils.filemanip import split_filename, fname_presuffix
import base_gui as bg
import nibabel
from numpy import zeros, nan_to_num, mean, logical_and, eye, dot
from scipy.ndimage import affine_transform
import numpy as np

sys.path.insert(0, '/home/jagust/cindeem/CODE/GraphicalAnalysis/pyGA')
import pyGraphicalAnalysis as pyga

def reslice_data(space_define_file, resample_file):
    """ reslices data in space_define_file to matrix of
    resample_file
    Parameters
    ----------
    space_define_file :  filename of space defining image
    resample_file : filename of image be resampled

    Returns
    -------
    img : space_define_file as nibabel image
    data : ndarray of data in resample_file sliced to
           shape of space_define_file
    """
    space_define_file = str(space_define_file)
    resample_file = str(resample_file)
    img = nibabel.load(space_define_file)
    change_img = nibabel.load(resample_file)
    T = eye(4)
    
    Tv = dot(np.linalg.inv(change_img.get_affine()), 
             dot(T, img.get_affine()))
    data = affine_transform(change_img.get_data().squeeze(), 
                            Tv[0:3,0:3], 
                            offset=Tv[0:3,3], 
                            output_shape = img.get_shape())

    return img, data


def realigntoframe1(niftilist):
    """given list of nifti files
    realigns to the 1st frame
    """
    startdir = os.getcwd()
    niftilist.sort()
    basepth, _ = os.path.split(niftilist[0])
    tmpdir, exists = bg.make_dir(basepth, 'realign_QA')
    if exists:
        return None, None
    # copy files to tmp dir
    copiednifti = []
    for f in niftilist:
        newf = bg.copy_file(f, tmpdir)
        copiednifti.append(str(newf))
    print 'copied nifti', copiednifti
    # realign to frame1
    os.chdir(tmpdir)
    rlgn = spm.Realign()
    rlgn.inputs.matlab_cmd = 'matlab-spm8'
    rlgn.inputs.in_files = copiednifti
    #print rlgn.mlab.cmdline
    rlgnout = rlgn.run()
    os.chdir(startdir)
    return rlgnout, copiednifti    


def realigntoframe17(niftilist):
    """given list of nifti files
    removes first 5 frames
    realignes rest to the 17th frame
    """
    startdir = os.getcwd()
    niftilist.sort()
    basepth, _ = os.path.split(niftilist[0])
    tmpdir, exists = bg.make_dir(basepth, 'realign_QA')
    if exists:
        return None, None    
    # copy files to tmp dir
    copiednifti = []
    for f in niftilist:
        newf = bg.copy_file(f, tmpdir)
        copiednifti.append(str(newf))
    # put files in correct order
    os.chdir(tmpdir)
    alteredlist =[x for x in  copiednifti]
    frame17 = alteredlist[16]
    alteredlist.remove(frame17)
    alteredlist = alteredlist[5:]
    alteredlist.insert(0, frame17)
    #print 'alteredlist', alteredlist
    # realign
    rlgn = spm.Realign(matlab_cmd='matlab-spm8')
    rlgn.inputs.in_files = alteredlist
    #rlgn.inputs.write_which = [2,0]
    #rlgn.register_to_mean = True
    rlgnout = rlgn.run()
    os.chdir(startdir)
    return rlgnout, copiednifti

def prefix_filename(infile, prefix=''):
    """prefixes a file and returns full path/newfilename
    """
    pth, nme = os.path.split(infile)
    newfile = os.path.join(pth, '%s%s'%(prefix,nme))
    return newfile

def touch_file(file):
    """ uses CommandLine to 'touch' a file,
    creating an empty exsisting file"""
    cmd = CommandLine('touch %s' % file)
    cout = cmd.run()
    return cout

def clean_nan(niftilist):
    """replaces nan in a file with zeros"""
    newfiles = []
    for item in niftilist:
        newitem = prefix_filename(item, prefix='nonan-')
        dat = nibabel.load(item).get_data().copy()
        affine = nibabel.load(item).get_affine()
        newdat = nan_to_num(dat)
        hdr = nibabel.Nifti1Header()
        newimg = nibabel.Nifti1Image(newdat, affine,hdr)
        newimg.to_filename(newitem)
        newfiles.append(newitem)
    return newfiles


def make_summed_image(niftilist, prefix='sum_'):
    """given a list of nifti files
    generates a summed image"""
    newfile = prefix_filename(niftilist[0], prefix=prefix)
    affine = nibabel.load(niftilist[0]).get_affine()
    shape =  nibabel.load(niftilist[0]).get_shape()
    newdat = zeros(shape)
    for item in niftilist:
        newdat += nibabel.load(item).get_data().copy()
    newimg = nibabel.Nifti1Image(newdat, affine)
    newimg.to_filename(newfile)
    return newfile

def make_pons_normed(petf, maskf, outfile):
    """given petf and maskf , normalize by mean of values
    in mask and save to outfile"""
    affine = nibabel.load(petf).get_affine()
    pet = nibabel.load(petf).get_data().squeeze()
    mask = nibabel.load(maskf).get_data().squeeze()
    if not pet.shape == mask.shape:
        raise AssertionError, 'pet and mask are different dimensions'
    allmask = logical_and(pet> 0, mask> 0)
    meanval = mean(pet[allmask])
    normpet = pet / meanval
    newimg = nibabel.Nifti1Image(normpet, affine)
    newimg.to_filename(outfile)


def simple_coregister(target, moving, other=None):
    """ uses the basic spm Coregister functionality to move the
    moving image to target, and applies to others is any"""
    startdir = os.getcwd()
    pth, _ = os.path.split(moving)
    os.chdir(pth)
    corg = spm.Coregister(matlab_cmd = 'matlab-spm8')
    corg.inputs.target = target
    corg.inputs.source = moving
    if other is not None:
        corg.inputs.apply_to_files = other
    corg_out = corg.run()
    os.chdir(startdir)
    return corg_out

def simple_warp(template, warped, other=None):
    """ uses basic spm Normalize to warp warped to template
    applies parameters to other if specified"""
    startdir = os.getcwd()
    pth, _ = os.path.split(warped)
    os.chdir(pth)
    warp = spm.Normalize(matlab_cmd = 'matlab-spm8')
    warp.inputs.template = template
    warp.inputs.source = warped
    if other is not None:
        warp.inputs.apply_to_files = other
    warp_out = warp.run()
    os.chdir(startdir)
    return warp_out

def simple_segment(mri):
    """uses spm to segment an mri in native space"""
    startdir = os.getcwd()
    pth, _ = os.path.split(mri)
    os.chdir(pth)
    seg = spm.Segment(matlab_cmd = 'matlab-spm8')
    seg.inputs.data = mri
    seg.inputs.gm_output_type = [False, False, True]
    seg.inputs.wm_output_type = [False, False, True]
    seg.inputs.csf_output_type = [False, False, True]
    segout = seg.run()
    os.chdir(startdir)
    return segout


def make_transform_name(inpet, inmri):
    """ given pet filename and mrifilename, makes
    the MRI_2_PET transform name"""
    pth, petnme = os.path.split(inpet)
    _, mrinme = os.path.split(inmri)

    mribase = mrinme.split('.')[0]
    petbase = petnme.split('.')[0]
    newnme = '%s_TO_%s.mat'%(mribase, petbase)
    newfile = os.path.join(pth, newnme)
    return newfile

def make_mean_20min(niftilist):
    """given list of niftis, grab frame 1-23
    generate mean image"""
    first_23 = niftilist[:23]
    first_23.sort()
    if not '23' in first_23[-1]:
        print "badframe numbers, unable to generate 20min mean"
        print 'frames', first_23
        return None
    newfile = make_mean(first_23, prefix='mean20min_')
    return newfile

def make_mean_40_60(niftilist):
    """given list of niftis, grab frame 28-31
    generate mean image"""
    #framen = [28,29,30,31]
    try:
        frames_28_31 = niftilist[27:31] #note frames start counting from 1
    except:
        print 'incorrect number of frames for making sum_40_60'
        return None
    if 'frame28' not in frames_28_31[0]:
        print 'bad frame numbers, unable to generate 40-60 mean'
        print 'frames', frames_28_31
        return None
    newfile = make_mean(frames_28_31, prefix='mean40_60min_')
    return newfile


def make_mean_usrdefined(niftilist, start, end):
    """ given nifti list generate mean image from
    start frame<start> to end frame<end>  inclusive
    name based on start and end frame numbers
    error raise if frame numbers not found in niftilist
    no check for missing frames between start and end"""
    niftilist.sort()
    # find indicies for the start and end frames in list
    for val, item in enumerate(niftilist):
        if 'frame' + repr(start).zfill(2) in item:
            start_frame = val
        if 'frame' + repr(end).zfill(2) in item:
            end_frame = val + 1 #add one to make sure we include frame
    frames = niftilist[start_frame:end_frame]
    prefix = 'mean_frame' + repr(start).zfill(2) + \
             '_to_frame' +repr(end).zfill(2) + '_'
    newfile = make_mean(frames, prefix = prefix)
    return newfile


def make_mean(niftilist, prefix='mean_'):
    """given a list of nifti files
    generates a mean image"""
    n_images = len(niftilist)
    newfile = prefix_filename(niftilist[0], prefix=prefix)
    affine = nibabel.load(niftilist[0]).get_affine()
    shape =  nibabel.load(niftilist[0]).get_shape()
    newdat = zeros(shape)
    for item in niftilist:
        newdat += nibabel.load(item).get_data().copy()
    newdat = newdat / n_images
    newimg = nibabel.Nifti1Image(newdat, affine)
    newimg.to_filename(newfile)
    return newfile

    
def invert_coreg(mri, pet, transform):
    """ coregisters pet to mri, inverts parameters
    and applies to mri"""
    startdir = os.getcwd()
    pth, _ = os.path.split(pet)
    os.chdir(pth)
    mlab_cmd = mlab.MatlabCommand(matlab_cmd='matlab-spm8')
    mlab_cmd.inputs.nodesktop = True
    mlab_cmd.inputs.nosplash = True
    mlab_cmd.inputs.mfile = True
    mlab_cmd.inputs.script_file = 'pyspm8_invert_coreg.m'
    script = """
    pet = \'%s\';
    mri = \'%s\';
    petv = spm_vol(pet);
    mriv = spm_vol(mri);
    x = spm_coreg(petv, mriv);
    M = inv(spm_matrix(x(:)'));
    save( \'%s\' , \'M\' );
    mrispace = spm_get_space(mri);
    spm_get_space(mri, M*mrispace);
    """%(pet,
         mri,
         transform)
    mlab_cmd.inputs.script = script
    mout = mlab_cmd.run()
    os.chdir(startdir)
    return mout

def forward_coreg(mri, pet, transform):
    """ coregisters pet to mri and applies to pet,
    saves parameters in transform """
    startdir = os.getcwd()
    pth, _ = os.path.split(pet)
    os.chdir(pth)
    mlab_cmd = mlab.MatlabCommand(matlab_cmd='matlab-spm8')
    mlab_cmd.inputs.nodesktop = True
    mlab_cmd.inputs.nosplash = True
    mlab_cmd.inputs.mfile = True
    mlab_cmd.inputs.script_file = 'pyspm8_invert_coreg.m'
    script = """
    pet = \'%s\';
    mri = \'%s\';
    petv = spm_vol(pet);
    mriv = spm_vol(mri);
    x = spm_coreg(petv, mriv);
    M = spm_matrix(x(:)');
    save( \'%s\' , \'M\' );
    petspace = spm_get_space(pet);
    spm_get_space(pet, M * petspace);
    """%(pet,
         mri,
         transform)
    mlab_cmd.inputs.script = script
    mout = mlab_cmd.run()
    os.chdir(startdir)
    return mout
    
    


def apply_transform_onefile(transform,file):
    """ applies transform to files using spm """
    startdir = os.getcwd()
    pth, _ = os.path.split(file)
    os.chdir(pth)
    mlab_cmd = mlab.MatlabCommand(matlab_cmd = 'matlab-spm8')
    mlab_cmd.inputs.nodesktop = True
    mlab_cmd.inputs.nosplash = True
    mlab_cmd.inputs.mfile = True
    mlab_cmd.inputs.script_file = 'pyspm8_apply_transform.m'
    script = """
    infile = \'%s\';
    transform = load(\'%s\');
    imgspace = spm_get_space(infile);
    spm_get_space(infile ,transform.M*imgspace);
    """%(file, transform)
    mlab_cmd.inputs.script = script
    mout = mlab_cmd.run()
    os.chdir(startdir)
    return mout
    

def reslice(space_define, infile):
    """ uses spm_reslice to resample infile into the space
    of space_define, assumes they are already in register"""
    startdir = os.getcwd()
    pth, _ = os.path.split(infile)
    os.chdir(pth)
    mlab_cmd = mlab.MatlabCommand(matlab_cmd = 'matlab-spm8')
    mlab_cmd.inputs.nodesktop = True
    mlab_cmd.inputs.nosplash = True
    mlab_cmd.inputs.mfile = True
    mlab_cmd.inputs.script_file = 'pyspm8_reslice.m'
    script = """
    flags.mean = 0;
    flags.which = 1;
    flags.mask = 1;
    flags.interp = 4;
    infiles = strvcat(\'%s\', \'%s\');
    invols = spm_vol(infiles);
    spm_reslice(invols, flags);
    """%(space_define, infile)
    mlab_cmd.inputs.script = script
    mout = mlab_cmd.run()
    os.chdir(startdir)
    return mout


def find_single_file(searchstring):
    """ glob for single file using searchstring
    if found returns full file path """
    file = glob(searchstring)
    if len(file) < 1:
        print '%s not found' % searchstring
        return None
    else:
        outfile = file[0]
        return outfile


def run_logan(subid, nifti, ecat, refroi, outdir):
    """run pyGraphicalAnalysis Logan Plotting on PIB frames
    """
    midframes,frametimes = pyga.get_midframes_fromecat(ecat, units='sec')
    data = pyga.get_data(nifti)
    ref = pyga.get_ref(refroi, data)
    int_ref = pyga.integrate_reference(ref,midframes)
    #Make DVR
    ki, vd, resids = pyga.integrate_data_genki(data,ref,
                                               int_ref,
                                               midframes,
                                               0.15, (35,90))
    pth, _ = os.path.split(nifti[0])
    _, refnme = os.path.split(refroi)
    refbase = refnme.split('.')[0]
    ref_plot = os.path.join(outdir, '%s_REF_TAC.png'%(refbase))
    pyga.save_inputplot(ref_plot, ref, midframes)
    pyga.pylab.clf()
    pyga.save_data2nii(ki, nifti[0],
                       '%s_dvr_%s'%(subid, refbase), outdir)
    pyga.save_data2nii(resids, nifti[0],
                       filename='resid_%s'%(refbase),
                       outdir=outdir)
    outfile = os.path.join(outdir, '%s_dvr.nii'%(refbase))
    data.close()
    return outfile

def fsl_mask(infile, mask, outname='grey_cerebellum_tu.nii'):
    """use fslmaths to mask img with mask"""

    pth, nme = os.path.split(infile)
    outfile = os.path.join(pth, outname)
    c1 = CommandLine('fslmaths %s -mas %s %s'%(infile, mask, outfile))
    out = c1.run()
    
    if not out.runtime.returncode == 0:
        print 'failed to mask %s'%(infile)
        print out.runtime.stderr
        return None
    else:
        return outfile

def fsl_theshold_mask(infile, gmmask, threshold, outname='gmaskd_mask.nii.gz'):
    """ use fslmaths to mask infile with gmmask which will be thresholded
    at threshold and saved into outname"""
    pth, nme = os.path.split(infile)
    outfile = os.path.join(pth, outname)
    c1 = CommandLine('fslmaths %s -thr %2.2f -mul %s %s'%(gmmask,
                                                          threshold,
                                                          infile,
                                                          outnfile)
                     )
    if not c1.runtime.returncode == 0:
        print 'gm masking of mask failed for %s'%(infile)
        return None
    return outfile
    
def extract_stats_fsl(data, mask, gmmask, threshold=0.3):
    """ uses fsl tools to extract data values in mask,
    masks 'mask' with gmmask thresholded at 'threshold' (default 0.3)
    returns mean, std, nvoxels
    NOTE: generates some tmp files in tempdir, but also removes them"""
    tmpdir = tempfile.mkdtemp()
    startdir = os.getcwd()
    os.chdir(tmpdir)
    # first mask mask with thresholded gmmask
    pth, nme = os.path.split(mask)
    outfile = fname_presuffix(mask, prefix = 'gmask_', newpath=tmpdir )
    c1 = CommandLine('fslmaths %s -thr %2.2f -nan -mul %s %s'%(gmmask,
                                                               threshold,
                                                               mask,
                                                               outfile)
                     ).run()
    if not c1.runtime.returncode == 0:
        print 'gm masking of mask failed for %s'%(mask)
        print 'tmp dir', tmpdir
        print c1.runtime.stderr
        return None   
    #first mask data
    cmd = 'fslmaths %s -nan -mas %s masked_data'%(data, outfile)
    mask_out = CommandLine(cmd).run()
    if not mask_out.runtime.returncode == 0:
        print 'masking failed for %s'%(data)
        return None, None, None
    masked = find_single_file('masked*')
    # get stats
    mean_out = CommandLine('fslstats %s -M'%(masked)).run()
    mean = mean_out.runtime.stdout.strip('\n').strip()
    std_out = CommandLine('fslstats %s -S'%(masked)).run()
    std = std_out.runtime.stdout.strip('\n').strip()
    vox_out = CommandLine('fslstats %s -V'%(masked)).run()
    vox = vox_out.runtime.stdout.split()[0]
    os.chdir(startdir)
    rmtree(tmpdir)
    return mean, std, vox


def fs_generate_dat(pet, subdir):
    """ use freesurfer tkregister to generate a dat file used in
    extracting PET counts with a labelled mri mask in freesurfer

    Parameters
    ----------
    pet : pet file that is registered to the subjects mri

    subdir : subjects freesurfer directory

    Returns
    -------
    dat : dat file generated , or None if failes
    you can check dat with ...
               'tkmedit %s T1.mgz -overlay %s -overlay-reg %s
               -fthresh 0.5 -fmid1'%(subject, pet, dat)
                 
    """
    pth, nme, ext = split_filename(pet)
    dat = os.path.join(pth, '%s_2_FS.dat'%(nme))
    cmd = 'tkregister2 --mov %s --s %s --regheader --reg %s --noedit'%(pet,
                                                                       subdir,
                                                                       dat)
    cout = CommandLine(cmd).run()
    if not cout.runtime.returncode == 0:
        print 'tkregister failed for %s'%(pet)
        return None
    return dat

def fs_extract_label_rois(subdir, pet, dat, labels):
    """
    Uses freesurfer tools to extract

    Parameters
    -----------
    subdir : subjects freesurfer directory

    pet : filename of subjects PET volume coreg'd to mri space

    dat : filename of dat generated by tkregister mapping pet to mri

    labels : filename of subjects aparc+aseg.mgz

    Returns
    -------
    stats_file: file  that contains roi stats

    label_file : file of volume with label rois in pet space
               you can check dat with ...
               'tkmedit %s T1.mgz -overlay %s -overlay-reg %s
               -fthresh 0.5 -fmid1'%(subject, pet, dat)
                 
    """
    pth, nme, ext = split_filename(pet)
    pth_lbl, nme_lbl, ext_lbl = split_filename(labels)
    
    stats_file = os.path.join(pth, '%s_%s_stats'%(nme, nme_lbl))
    label_file = os.path.join(pth, '%s_%s_.nii.gz'%(nme, nme_lbl))

    # Gen label file
    cmd = ['mri_label2vol',
           '--seg %s/mri/%s'%(subdir, labels),
           '--temp %s'%(pet),
           '--reg'%(dat),
           '--o %s'%(label_file)]
    cmd = ' '.join(cmd)
    cout = CommandLine(cmd).run()
    if not cout.runtime.returncode == 0:
        print 'mri_label2vol failed for %s'%(pet)
        return None, None
    ## Get stats
    cmd = ['mri_segstats',
           '--seg %s'%(label_file),
           '--sum %s'%(stats_file),
           '--in %s'%(pet),
           '--nonempty --ctab',
           '/usr/local/freesurfer_x86_64-4.5.0/FreeSurferColorLUT.txt']
    cmd = ' '.join(cmd)
    cout = CommandLine(cmd).run()
    if not cout.runtime.returncode == 0:
        print 'mri_segstats failed for %s'%(pet)
        return None, None
    return stats_file, label_file

    
def parse_fs_statsfile(statsfile):
    """opens a fs generated stats file and returns
    a dict of roi keys with [mean, std, nvox], for
    each roi
    """
    for line in open(statsfile):
        if line[0] == '#':
            continue
        tmp = line.split()
        roi = tmp[4]
        mean = eval(tmp[5])
        std = eval(tmp[6])
        nvox = eval(tmp[2])
        roidict.update({roi:[mean, std, nvox]})
    return roidict
