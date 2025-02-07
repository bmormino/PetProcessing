import wx
import sys, os
sys.path.insert(0, '/home/jagust/cindeem/CODE/ruffus')
import MultiDirDialog as mdd
from glob import glob

import nipype
from nipype.interfaces.base import CommandLine


def MyDirsDialog(prompt='Choose Subject Dirs',indir='',title='Choose Subject Dirs'):
      """
      Advanced  directory dialog and returns selected directories
      """
      dlg = mdd.MultiDirDialog(None,
                               message=prompt,
                               title=title,
                               defaultPath=indir)
      if dlg.ShowModal() == wx.ID_OK:
          tmpdir = dlg.GetPaths()
      else:
          tmpdir = []
      dlg.Destroy()
      return tmpdir


def FileDialog(prompt='ChooseFile', indir=''):
    """
    opens a wx dialog that allows you to select a single
    file, and returns the full path/name of that file """
    dlg = wx.FileDialog(None,
                        message = prompt,
                        defaultDir = indir)
                        
    if dlg.ShowModal() == wx.ID_OK:
          outfile = dlg.GetPath()
    else:
          outfile = None
    dlg.Destroy()
    return outfile

def FilesDialog(prompt = 'Choose Files', indir = ''):
      """
      opens a wx Dialog that allows you to select multiple files within
      a single directory and returns full path/names of those files"""
      fdlg = wx.FileDialog(None,
                           message=prompt,
                           defaultDir = indir,
                           style = wx.FD_MULTIPLE)
      if fdlg.ShowModal() == wx.ID_OK:
            outfiles = fdlg.GetPaths()
      else:
            outfiles = None
      fdlg.Destroy()
      return outfiles

def SimpleDirDialog(prompt='Choose Directory', indir=''):
    """
    opens a directory dialog and returns selected directory
    """
    sdlg = wx.DirDialog(None,
                        message = prompt,
                        defaultPath = indir)
    if sdlg.ShowModal() == wx.ID_OK:
          tmpdir = sdlg.GetPath()
    else:
          tmpdir = []
    sdlg.Destroy()
    return tmpdir
    
def MyVisitDialog():
    choices = ['v1', 'v2', 'v3', 'v4', 'v5']
    dialog = wx.SingleChoiceDialog(None,
                                   'Choose a Timepoint',
                                   'VISIT TIMEPOINT',
                                   choices)
    if dialog.ShowModal() == wx.ID_OK:
        visit = dialog.GetStringSelection()
    dialog.Destroy()
    return visit
    
def MyTracerDialog():
    choices = ['FDG', 'PIB']
    dialog = wx.SingleChoiceDialog(None,
                                   'Choose a Tracer',
                                   'TRACERS',
                                   choices)
    if dialog.ShowModal() == wx.ID_OK:
        tracer = dialog.GetStringSelection()
    dialog.Destroy()
    return tracer

def MyScanChoices(choices,message = 'Choose directories'):
    sdialog = wx.MultiChoiceDialog(None,
                                  message = message,
                                  caption='Choices',
                                  choices=choices)
    if sdialog.ShowModal() == wx.ID_OK:
        dirs = sdialog.GetSelections()
    sdialog.Destroy()
    return [choices[x] for x in dirs]


def MyRadioSelect(outdict):
      mrc = MyRadioChoices(outdict)
      mrc_retval = mrc.ShowModal()
      if mrc_retval == wx.ID_OK:
            outdict = mrc.GetValue()
      mrc.Destroy()
      return outdict

def MriDialog(subid):
      qdlg = wx.MessageDialog(None,
                              message = 'No Freesurfer MRI for ' + \
                              '%s, skip subject?'%(subid),
                              caption = 'MRI Message',
                              style=wx.YES_NO)
     
      if qdlg.ShowModal() == wx.ID_YES:
            resp = True

      else:
            resp = False
      
      qdlg.Destroy()
      return resp

class MyRadioChoices(wx.Dialog):
      
      def __init__(self, outdict):
            #global outdict
            self.outdict = outdict
            nchoices = len(outdict)
            wx.Dialog.__init__(self, None, -1, 'Radio select', size=(800,800),
                               )
            panel = wx.Panel(self,-1)
            self.button = wx.Button(panel, wx.ID_OK, 'Finished',
                                    pos = (10,10))
            self.Bind(wx.EVT_CLOSE, self.DialogClose)
            #self.scroll = wx.ScrolledWindow(panel, -1)
            #self.scroll.SetScrollbars( 100, 100, 600, nchoices*100) 
            dirlist = ['Controls', 'AD', 'LPA', 'PCA', 'FTLD', 'CBS',
                       'Others', 'NIFD-LBL', 'NIFD-ADNI', 'MCI']
            self.rb = {}
            for val, item in enumerate(sorted(outdict.keys())):
                  self.rb.update({item:wx.RadioBox(panel, -1, item, (10, 50+val*40),
                                                   (550,40), dirlist,
                                                   1, wx.RA_SPECIFY_ROWS)})

      def DialogClose(self, event):
            self.EndModal(wx.ID_OK)
      def GetValue(self):
            for key in self.rb:
                  self.outdict[key][1] = self.rb[key].GetStringSelection()
            #print self.outdict
            return self.outdict
                  
            
            
#### END WX ###

def make_subject_dict(dirs, outdict):
      """given a set of directories
      initialize a dictionary to hold
      names
      directories
      diagnoses
      """
      
      for item in dirs:
          scanid = item.strip('/home/jagust/arda/lblid')
          outdict.update({scanid:[item,None]})
      

def make_dir(base_dir, dirname='fdg_nifti'):
    """ makes a new directory if it doesnt alread exist
    returns full path
    
    Parameters
    ----------
    base_dir : str
    the root directory
    dirname  : str (default pib_nifti)
    new directory name
    
    Returns
    -------
    newdir  : str
    full path of new directory
    """
    newdir = os.path.join(base_dir,dirname)
    directory_exists = os.path.isdir(newdir)
    if not directory_exists:
        os.mkdir(newdir)
    return newdir, directory_exists

def make_rec_dir(base_dir, dirname='fdg_nifti'):
    """ makes a new directories recursively if it doesnt already exist
    returns full path
    
    Parameters
    ----------
    base_dir : str
    the root directory
    dirname  : str (default pib_nifti)
    new directory name
    
    Returns
    -------
    newdir  : str
    full path of new directory
    """
    newdir = os.path.join(base_dir,dirname)
    directory_exists = os.path.isdir(newdir)
    if not directory_exists:
        os.makedirs(newdir)
    return newdir, directory_exists






def remove_files(files):
    """removes files """
    if not hasattr(files, '__iter__'):
        cl = CommandLine('rm %s'% files)
        out = cl.run()
        if not out.runtime.returncode == 0:
            print 'failed to delete %s' % files
            print out.runtime.stderr
        return
    for f in files:
        cl = CommandLine('rm %s'% f)
        out = cl.run()
        if not out.runtime.returncode == 0:
            print 'failed to delete %s' % f
            print out.runtime.stderr
    
def copy_files(infiles, newdir):
    """wraps copy file to run across multiple files
    returns list"""
    newfiles = []
    for f in infiles:
        newf = copy_file(f, newdir)
        newfiles.append(newf)
    return newfiles

def copy_file(infile, newdir):
    """ copy infile to new directory
    return full path of new file
    """
    cl = CommandLine('cp %s %s'%(infile, newdir))
    out = cl.run()
    if not out.runtime.returncode == 0:
        print 'failed to copy %s' % infile
        print out.runtime.stderr
        return None
    else:
        basenme = os.path.split(infile)[1]
        newfile = os.path.join(newdir, basenme)
        return newfile

def convert(infile, outfile):
    """converts freesurfer .mgz format to nifti
    """
    c1 = CommandLine('mri_convert --out_orientation LAS %s %s'%(infile,
                                                                outfile))
    out = c1.run()
    if not out.runtime.returncode == 0:
        #failed
        print 'did not convert %s from .mgz to .nii'%(infile)
    else:
        path = os.path.split(infile)[0]
        niifile = os.path.join(path,outfile)
        return niifile


def ecat2nifti(ecat, newname):
    """run ecat_convert.py"""
    cmd = 'ecat_convert.py'
    format = '-format NIFTI'
    outname = '-newname %s'%(newname)
    cmdstr = ' '.join([cmd, format, outname,ecat])    
    cl = CommandLine(cmdstr)
    out = cl.run()
    if not out.runtime.returncode == 0:
        return False
    else:
        return True

def copy_dir(dir, dest, pattern='*'):
      """copies files matching pattern in dir to dest
      returns list of abspath to new copied items """
      items = glob('%s/%s'%(dir,pattern))
      newitems = []
      for item in items:
            newitem = copy_file(item, dest)
            newitems.append(newitem)
      return newitems


def unzip_file(infile):
    """ looks for gz  at end of file,
    unzips and returns unzipped filename"""
    base, ext = os.path.splitext(infile)
    if not ext == '.gz':
        return infile
    else:
        cmd = CommandLine('gunzip %s' % infile)
        cout = cmd.run()
        if not cout.runtime.returncode == 0:
            print 'Failed to unzip %s'%(infile)
            return None
        else:
            return base


def convertallecat(ecats, newname):
      """ converts all ecat files and removes .v files"""
      for f in ecats:
            ecat2nifti(f, newname)
            os.remove(f)

def move_and_convert(mgz, dest, newname):
      """takes a mgz file, moves it,
      converts it to nifti and then removes
      the original mgz file"""
      cwd = os.getcwd()
      new_mgz = copy_file(mgz, dest)
      os.chdir(dest)
      nii = convert(new_mgz, newname)
      os.chdir(cwd)
      os.remove(new_mgz)
      return nii

def make_brainstem(aseg):

      cwd = os.getcwd()
      pth, nme = os.path.split(aseg)
      os.chdir(pth)
      cl = CommandLine('fslmaths %s -thr 16 -uthr 16 brainstem'% (aseg))
      cout = cl.run()
      os.chdir(cwd)
      if not cout.runtime.returncode == 0:
            print 'Unable to create brainstem for %s'%(aseg)
            return None
      else:
            os.remove(aseg)
            return 'brainstem'

      
def make_whole_cerebellume(aseg):
      """
      os.system('fslmaths rad_aseg -thr 46 -uthr 47 whole_right_cerebellum')
      os.system('fslmaths rad_aseg -thr 7 -uthr 8 whole_left_cerebellum')
      os.system('fslmaths whole_left_cerebellum -add whole_right_cerebellum -bin whole_cerebellum')
      """
      cwd = os.getcwd()
      pth, nme = os.path.split(aseg)
      os.chdir(pth)
      cmd = 'fslmaths %s -thr 46 -uthr 47 whole_right_cerebellum'%(aseg)
      cl = CommandLine(cmd)
      cout = cl.run()
      if not cout.runtime.returncode == 0:
            os.chdir(cwd)
            print 'Unable to create  right whole cerebellum for %s'%(aseg)
            return None
      
      cmd = 'fslmaths %s -thr 7 -uthr 8 whole_left_cerebellum'%(aseg)
      cl2 = CommandLine(cmd)
      cout2 = cl2.run()
      if not cout2.runtime.returncode == 0:
            os.chdir(cwd)
            print 'Unable to create  whole left cerebellum for %s'%(aseg)
            return None     

      cmd = 'fslmaths whole_left_cerebellum -add whole_right_cerebellum' + \
            ' -bin whole_cerebellum'
      cl3 = CommandLine(cmd)
      cout3 = cl3.run()
      if not cout3.runtime.returncode == 0:
            os.chdir(cwd)
            print 'Unable to create  whole cerebellum for %s'%(aseg)
            print cout3.runtime.stderr
            print cout3.runtime.stdout
            return None     
      cmd = 'rm whole_right_cerebellum.* whole_left_cerebellum.*'
      cl4 = CommandLine(cmd)
      cout4 = cl4.run()      
      whole_cerebellum = glob('%s/whole_cerebellum.*'%(pth))
      os.chdir(cwd)
      return whole_cerebellum[0]
      
def make_cerebellum(aseg):
      cwd = os.getcwd()
      pth, nme = os.path.split(aseg)
      os.chdir(pth)
      cl = CommandLine('fslmaths %s -thr 47 -uthr 47 right_cerebellum'% (aseg))
      cout = cl.run()
      
      if not cout.runtime.returncode == 0:
            os.chdir(cwd)
            print 'Unable to create  right cerebellum for %s'%(aseg)
            return None

      cl2 = CommandLine('fslmaths %s -thr 8 -uthr 8 left_cerebellum'% (aseg))
      cout2 = cl2.run()

      if not cout2.runtime.returncode == 0:
            os.chdir(cwd)
            print 'Unable to create  left cerebellum for %s'%(aseg)
            return None

      cl3 = CommandLine('fslmaths left_cerebellum -add right_cerebellum -bin grey_cerebellum')
      cout3 = cl3.run()
      if not cout3.runtime.returncode == 0:
            print 'Unable to create whole cerebellum for %s'%(aseg)
            print cout3.runtime.stderr
            print cout3.runtime.stdout
            return None
      
      cmd = 'rm right_cerebellum.* left_cerebellum.*'
      cl4 = CommandLine(cmd)
      cout4 = cl4.run()
      os.chdir(cwd)
      cerebellum = glob('%s/grey_cerebellum.*'%(pth))
      return cerebellum[0]

      
if __name__ == '__main__':

    root = '/home/jagust/cindeem/tmpucsf'
    mridir = '/home/jagust/UCSF/freesurfer'
    app = wx.App()
    
    tracer = MyTracerDialog()
    print tracer
    subs = MyDirsDialog(prompt='Choose Subjectss ',
                        indir='/home/jagust/arda/lblid')
    alldirs = []
    for s in subs:
        dirs = glob('%s/%s*'%(s,tracer))
        alldirs.extend(dirs)
    
    finalchoice = MyScanChoices(alldirs)
    #global outdict
    outdict = {}
    make_subject_dict(finalchoice,outdict) 
    MyRadioChoices(outdict).Show()
    app.MainLoop()
    """
    for item in outdict:
        if outdict[item][1] is None:
              continue
        else:
              petdir, dx = outdict[item]
        subid, _ = os.path.split(item)
        print subid
        # check for and Make Target Directories
        basedir = os.path.join(root, '%s-spm8'%(dx))
        subdir, _ = make_dir(basedir, dirname=subid)
        tracerdir, already_exists = make_dir(subdir, dirname = '%s_nifti' % (tracer.lower()) )
        if already_exists:
              print '%s already has %s dir, remove all related dirs if you want to redo' % (subid, tracer)
              print 'skipping %s' %(subid)
              continue
        rawdatadir, _  = make_dir(subdir, dirname = 'RawData')
        rawtracer, _  = make_dir(rawdatadir, dirname = tracer)
        anatomydir, anat_exists  = make_dir(subdir,dirname='fs_anatomy')
        masksdir, _  = make_dir(tracerdir,dirname='ref_region')
        print 'directories created for %s' % subid
        
        # Copy PET data, convert to nifti
        newraw = copy_dir(petdir, rawtracer)
        ecats = copy_dir(rawtracer, tracerdir, pattern='*.v')
        newname = '%s_%s' % (subid, tracer)
        convertallecat(ecats, newname)
        print 'ecats converted for %s ' % subid

        # Get MRI, convert
        if not anat_exists:
              mri = os.path.join(mridir, subid, 'mri', 'nu.mgz')
              mri_nii = move_and_convert(mri, anatomydir, 'rad_nu_mri.nii')
              print 'mri converted'
        # Get aseg, convert
        aseg = os.path.join(mridir, subid, 'mri', 'aseg.mgz')
        aseg_nii = move_and_convert(aseg, masksdir, 'rad_aseg.nii')
        
        # Generate reference Region
        if tracer == 'FDG':
            make_brainstem(aseg_nii)
            print 'brainstem created for %s' % subid
        else:
            make_cerebellum(aseg_nii)
            print 'cerebellum created for %s ' % subid
    """
