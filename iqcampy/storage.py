# AUTOGENERATED! DO NOT EDIT! File to edit: ../notebooks/10_reading-iqcam-data.ipynb.

# %% auto 0
__all__ = ['download', 'filetree', 'read_darkref', 'read_whiteref', 'read_capture', 'read_reflectance', 'compute_reflectance']

# %% ../notebooks/10_reading-iqcam-data.ipynb 26
import os 
import shutil 
import requests
from tqdm import tqdm 

from treelib import Tree
from os import walk 
from pathlib import Path 
import re 
import glob 

import numpy as np
import matplotlib.pyplot as plt


# %% ../notebooks/10_reading-iqcam-data.ipynb 27
def download(): 
    '''Download Specim IQcam demo dataset zipfile and extract its contents. '''
    
    # check if 'downloads' folder is current working directory   
    
    cwd = os.path.basename(os.getcwd()) 
    
    if cwd != 'downloads': 
        os.makedirs('downloads', exist_ok=True)
        os.chdir('downloads') 
        cwd = os.path.basename(os.getcwd()) 
        
    print(f'Current working directory: "{cwd}"')
    
    # download zipfile 
    
    zip_file = 'iqcam_2021-02-03_005_4x-aquarelblauw-FL-01.zip' 
    url = f'https://f002.backblazeb2.com/file/iqcampy-demo/{zip_file}' 
    data_path = re.sub('\.zip$', '', zip_file) # remove extension .zip 
    
    if os.path.exists(zip_file): 
        print(f'(1/2) Found existing zipfile: {zip_file} (skipping download)')
        
    else: 
        print('(1/2) Please wait while downloading...')

        r = requests.get(url, stream=True)
        total = int(r.headers.get('content-length', 0))

        # Can also replace 'file' with a io.BytesIO object
        with open(zip_file, 'wb') as fh, tqdm(
            desc=zip_file,
            total=total,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
            ) as bar:
                for data in r.iter_content(chunk_size=1024):
                    size = fh.write(data)
                    bar.update(size)

    #extracting zipfile 
    print('(2/2) Extracting zip file...')
    shutil.unpack_archive(zip_file)
    print('Ready!')
        
    return data_path
    

    
def filetree(data_path, include_files=True, force_absolute_ids=True, show=True):
    """Prints a file tree with the contents of the `data_path` folder. 
    
    """ 
    
    tree = Tree()
    first = True
    for root, _, files in walk(data_path):
        p_root = Path(root)
        if first:
            parent_id = None
            first = False
        else:
            parent = p_root.parent
            parent_id = parent.absolute() if force_absolute_ids else parent

        p_root_id = p_root.absolute() if force_absolute_ids else p_root
        tree.create_node(tag="%s/" % (p_root.name if p_root.name != "" else "."),
                         identifier=p_root_id, parent=parent_id)
        if include_files:
            for f in files:
                f_id = p_root_id / f
                tree.create_node(tag=f_id.name, identifier=f_id, parent=p_root_id) 

    # fix treelib.tree.show() bug: 
    # see: https://stackoverflow.com/questions/46345677/treelib-prints-garbage-instead-of-pseudographics-in-python3 

    tree_str = tree.show(stdout=False)
    if show: 
        print(tree_str)
    
    return None




def read_darkref(data_path): 
    '''Read DARKREF header and data. 
    
    Returns: meta, nms, dark_spectrum
    '''
    
    # darkref filepaths      
    darkref_hdr = glob.glob(f'{data_path}/**/DARKREF*.hdr', recursive=True)[0]
    darkref_raw = glob.glob(f'{data_path}/**/DARKREF*.raw', recursive=True)[0] 

    #darkref data
    with open(darkref_hdr) as fh: 
        txt = fh.read()
        arr = np.fromfile(darkref_raw, dtype=np.uint16) 
        
    ptrn = '(?P<meta>.*)wavelength\s+=\s+\{(?P<nms>.*)\}'
    repl_meta = '\g<meta>'
    repl_nms = '\g<nms>'
    
    nms = re.sub(ptrn, repl_nms, txt, flags=re.DOTALL)
    nms = re.sub('\n', '', nms)
    nms = re.sub('\s', '', nms)
    nms = re.split(',', nms)
    nms = np.array([float(n) for n in nms])
    
    meta = re.sub(ptrn, repl_meta, txt, flags=re.DOTALL)  
    
    dark = np.mean(arr).round(1) # single dark current for all pixels 
    
    dark_spectrum = dark * np.ones_like(nms) 
        
    return meta, nms, dark_spectrum



def read_whiteref(data_path): 
    '''Read WHITEREF header and data. 
    
    Returns: meta, nms, white_spectrum
    '''
    
    # whiteref filepaths      
    whiteref_hdr = glob.glob(f'{data_path}/**/WHITEREF*.hdr', recursive=True)[0]
    whiteref_raw = glob.glob(f'{data_path}/**/WHITEREF*.raw', recursive=True)[0] 

    #darkref data
    with open(whiteref_hdr) as fh: 
        txt = fh.read()
        arr = np.fromfile(whiteref_raw, dtype=np.uint16) 
        
    ptrn = '(?P<meta>.*)wavelength\s+=\s+\{(?P<nms>.*)\}'
    repl_meta = '\g<meta>'
    repl_nms = '\g<nms>'
    
    nms = re.sub(ptrn, repl_nms, txt, flags=re.DOTALL)
    nms = re.sub('\n', '', nms)
    nms = re.sub('\s', '', nms)
    nms = re.split(',', nms)
    nms = np.array([float(n) for n in nms])
    
    meta = re.sub(ptrn, repl_meta, txt, flags=re.DOTALL)  
    
    white_spectrum = arr.reshape([204, 512]).mean(axis=1)  
        
    return meta, nms, white_spectrum 


def read_capture(data_path): 
    '''Read cube capture header and data. 
    
    Returns: meta, nms, capture_cube
    '''
    
    # capture filepaths      
    capture_hdr = glob.glob(f'{data_path}/**/iqcam*.hdr', recursive=True)[0]
    capture_raw = glob.glob(f'{data_path}/**/iqcam*.raw', recursive=True)[0] 

    #darkref data
    with open(capture_hdr) as fh: 
        txt = fh.read()
        arr = np.fromfile(capture_raw, dtype=np.uint16) 
        
    ptrn = '(?P<meta>.*)wavelength\s+=\s+\{(?P<nms>.*)\}'
    repl_meta = '\g<meta>'
    repl_nms = '\g<nms>'
    
    nms = re.sub(ptrn, repl_nms, txt, flags=re.DOTALL)
    nms = re.sub('\n', '', nms)
    nms = re.sub('\s', '', nms)
    nms = re.split(',', nms)
    nms = np.array([float(n) for n in nms])
    
    meta = re.sub(ptrn, repl_meta, txt, flags=re.DOTALL)  
    
    #capture_cube = arr.reshape([512, 204, 512])[::-1, ::-1, ::-1].transpose([2, 0, 1]).astype(float) 
    capture_cube = arr.reshape([512, 204, 512]).transpose([2, 0, 1])[:, ::-1, :].astype(float) 
        
    return meta, nms, capture_cube



def read_reflectance(data_path): 
    '''Read precomputed computed reflectance header, cube data and rgb image. 
    
    Returns: meta, nms, reflectance_cube, rgb_img
    '''
    
    # reflectance filepaths (assuming only one extracted zip file)    
    reflectance_hdr = glob.glob(f'{data_path}/**/REFLECTANCE*.hdr', recursive=True)[0]
    reflectance_dat = glob.glob(f'{data_path}/**/REFLECTANCE*.dat', recursive=True)[0] 
    png = glob.glob(f'{data_path}/**/REFLECTANCE*.png', recursive=True)[0]

    #reflectance data
    with open(reflectance_hdr) as fh: 
        txt = fh.read()
        arr = np.fromfile(reflectance_dat, dtype=np.float32) 
        rgb_img = plt.imread(png)
        
    ptrn = '(?P<meta>.*)wavelength\s+=\s+\{(?P<nms>.*)\}'
    repl_meta = '\g<meta>'
    repl_nms = '\g<nms>'
    
    nms = re.sub(ptrn, repl_nms, txt, flags=re.DOTALL)
    nms = re.sub('\n', '', nms)
    nms = re.sub('\s', '', nms)
    nms = re.split(',', nms)
    nms = np.array([float(n) for n in nms])
    
    meta = re.sub(ptrn, repl_meta, txt, flags=re.DOTALL)  
    
    reflectance_cube = arr.reshape([512, 204, 512]).transpose([2, 0, 1])[:, ::-1, :] 
    #reflectance_cube = reflectance_cube[:,:,::-1]
        
    return meta, nms, reflectance_cube, rgb_img   


def compute_reflectance(capture_cube, dark_spectrum, white_spectrum): 
    '''Compute spectral reflectance cube from raw data. 
    
    Returns: reflectance_cube
    '''
    
    reflectance_cube = (capture_cube - dark_spectrum[None, None, :]) /\
                                (white_spectrum[None, None,:] - dark_spectrum[None, None,:])
        
    return reflectance_cube 
