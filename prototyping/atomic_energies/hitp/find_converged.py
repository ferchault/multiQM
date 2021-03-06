#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug  5 14:32:08 2019

@author: misa
"""

import glob
import os
from parse import parse_log_file
import pandas as pd
import numpy as np

def get_tree(path, depth):
    """
    returns the paths to the subdirectories with depth
    """
    if depth==3:
        return(glob.glob(path+'/*/*/*/'))
    elif depth==2:
        return(glob.glob(path+'/*/*/'))
    else:
        raise Exception("Depth not implemented!")
        

def get_status(dirs, dest, save_df=False, write=True):
    """
    determine the status of calculation from their log-files, returns a tuple of lists
    every element of the tuple describes one status (broken, converged, restart...)
    each element of the tuple contains all directories with the same status
    
    dirs: list of paths to log-files
    dest: path to destination where the output files are written
    save_df: save pandas Dataframes made from the log-files in the corresponding log-file directories
    write: if True writes the status to files in dest, otherwise the results are returned as a tuple of lists
    """
    
    # get status for every directory in dirs
    ready2cube = []
    revise = []
    restart = []
    broken = []
    other = []
    for d in dirs:
        status, gemax, num_it = parse_log_file(os.path.join(d,'run.log'), save=save_df)
        if status == 'finished' and gemax < 1e-6:
            ready2cube.append(d)
        elif status == 'finished' and gemax > 1e-5:
            restart.append(d)
        elif status == 'finished' and gemax > 1e-6 and gemax < 1e-5: # maybe if more than 1000 iterations change to ready2cube
            revise.append(d)
        elif status == 'broken':
            broken.append(d+'\t'+gemax)
        elif status == "Running, not started or broken":
            other.append(d)
    
    # write results to files or return as lists
    if write:
        with open(os.path.join(dest, 'ready2cube'), 'w') as fs:
            for item in ready2cube:
                fs.write("%s\n" % item)
                
        with open(os.path.join(dest, 'restart'), 'w') as fs:
            for item in restart:
                fs.write("%s\n" % item)
                
        with open(os.path.join(dest, 'broken'), 'w') as fs:
            for item in broken:
                fs.write("%s\n" % item)
        
        with open(os.path.join(dest, 'other'), 'w') as fs:
            for item in other:
                fs.write("%s\n" % item)

        with open(os.path.join(dest, 'revise'), 'w') as fs:
            for item in revise:
                fs.write("%s\n" % item)

    else:
        return(ready2cube, restart, broken, other, revise)
           
def concatenate_files(file_paths):
    """
    concatenates lines of all the files and returns one list with elements as lines of the files
    """
    output = []
    for file in file_paths:
        with open(file, 'r') as f:
            for line in f:
                line=line.rstrip('\n')
                output.append(line)
    return(output)
            
def find_compounds_finished(dirs):
    """
    dirs: absolute path on scicore to every log-file
    count the number of occurences of each compound and return path if >=5 (all calculations are converged)
    """
    # isolate name of compound from paths and store in list
    comp_names = []
    comp_names_ve = []
    for idx, el in enumerate(dirs):
        splitted = el.split('/')[9:12]
        splitted[1] = '#'
        comp_name_ve = splitted[0]+splitted[1]+splitted[2]
        comp_names_ve.append(comp_name_ve)
        comp_names.append(splitted[0])
        
    # count the number of occurences of each compound and return path if ==5 (all calculations are converged)
    # set returns the names of the compunds (every unique name)
    all_finished = [] # compounds for which all calculations are converged
    for compound in set(comp_names):
        occurences = 0
        for num_ve in ['#ve_8', '#ve_15','#ve_23', '#ve_30', '#ve_38']:
           sub_occ = comp_names_ve.count(compound+num_ve)
           if sub_occ > 0:
               occurences += 1
        
#        assert occurences > 5, "More occurences than lambda-values"
        if occurences == 5:
            compound = './' + compound + '/' # build relative path
            all_finished.append(compound)
        if occurences > 5:
            print(compound, 'number of occurence = ', occurences)

    return(all_finished)
    
def unified_convergence_lambda(path, lam_ve, save=None):
    """
    return concatenated Dataframes for convergence for one compound for one lambda value over several restarts
    path: path to compound
    lam_ve: lambda value given in valence electrons as a string for which dataframes will be concatenated
    save: path where concatenated fill will be saved
    """
    # sorted paths to all parsed log-files (pandas Dataframe) with the same lambda-value
    direc = path + '/*/' + 've_' + lam_ve + '/parsed_run.log'
    direc = glob.glob(direc)
    direc.sort()
    
    df = pd.read_csv(direc[0], sep='\t')
    # read log-files and append content to list
    for idx, log_f in enumerate(direc):
        if idx!=0:
            tmp = pd.read_csv(log_f, sep='\t')
            tmp['NFI'] = tmp['NFI']+df['NFI'][len(df['NFI'])-1]
            df = pd.concat([df, tmp])
            
    if save:
        df.to_csv(save, sep='\t', header=True, index=False)
    else:
        return(df)
                
def order_cubes(dirs, ordering='old'):
    """
    for every directory
    rename and move cube-files for every lambda value in new subdirectory
    
    dirs: paths to all compounds
    """
    
    for path in dirs:
    
        # single compound
        if not os.path.exists(os.path.join(path, 'cube-files')):
            os.mkdir(os.path.join(path, 'cube-files'))
        else:
            print('Warning, {} exists already!'.format(os.path.join(path, 'cube-files')))
        
        # get paths to the cube files
        paths_cube_files = glob.glob(path + '/*/*/DENSITY.cube')
        #sort paths to ensure that the cube-files from the last run is selected if several cube-files exist
        paths_cube_files.sort()
        keys = ['ve_'+str(el) for el in np.arange(39)]
        items = ['']*len(keys)
        cube_dict = dict(zip(keys, items))
 #       cube_dict = {'ve_2':'', 've_4':'','ve_6':'', 've_8':'','ve_10':'', 've_12':'', 've_14':'', 've_15':'', 've_23':'', 've_30':'', 've_38':''}
        for pcf in paths_cube_files:
            
            if ordering == 'new':
                num_ve = pcf.split('/')[len(pcf.split('/'))-3]
            else:
                num_ve = pcf.split('/')[len(pcf.split('/'))-2]
            
            cube_dict[num_ve] = pcf
    
        for num_ve, pcf in cube_dict.items():
            # rename and move cube-file
            if pcf != '':
                new_path = os.path.join(path, 'cube-files/' + num_ve + '.cube')
                os.rename(pcf, new_path)
        
    
def mv_cubes(p2cs):
    """
    p2cs: paths to the cube-files that will be moved to ./dsgdb9nsd_xxxxxx/cube-files, items should have the form ./dsgdb9nsd_xxxxxx/run_x/ve_x/DENSITY.cube
    """
    
    for pc in p2cs:
        # isolate path to compound from full path to cube-file
        path2compound = pc.split('/')[:-3]
        path2compound = '/'.join(path2compound)
        # make ./dsgdb9nsd_xxxxxx/cube-files if not exists
        if not os.path.exists(os.path.join(path2compound, 'cube-files')):
            os.mkdir(os.path.join(path2compound, 'cube-files'))
        else:
            print('Warning, {} exists already!'.format(os.path.join(path2compound, 'cube-files')))
        
        # get lambda value of cube-file expressed in VE
        num_ve = pc.split('/')[-2]
        # create new file name and move cube-file
        new_path = os.path.join(path2compound, 'cube-files/' + num_ve + '.cube')
        os.rename(pc, new_path)
        
def read_list_from_file(file):
    list_items = []
    with open(file, 'r') as f:
        for line in f:
            list_items.append(line.strip('\n'))
            
    return(list_items)

def write_list_to_file(l, file):
    with open(file, 'w') as f:
        for line in l:
            f.write(line + '\n')
    
def check_input(input_as_list, entry):
    """
    checks if entry is a line in the list (the input file where every line is an entry)
    """
    in_file = None
    for item in input_as_list:
        item_without_comment = item.split('#')[0]
        if entry == item_without_comment:
            in_file = True
            break
        else:
            in_file = False
    return(in_file)

def correct_inps(paths):
    """
    reports if input files contain line '  RESTART WAVEFUNCTION LATEST'
    paths: paths to run.inp-files
    """
    restart_exist = []
    restart_dexist = []
    for r in paths:
        inp=read_list_from_file(r)
        if check_input(inp, '  RESTART WAVEFUNCTION LATEST'):
            restart_exist.append(r)
        else:
            restart_dexist.append(r)
    return(restart_exist, restart_dexist)
    




