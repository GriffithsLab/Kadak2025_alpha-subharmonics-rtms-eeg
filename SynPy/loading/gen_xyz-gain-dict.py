import SynPy as sp

import os
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import matplotlib.patches as patches
# import matplotlib.cm as cm
import re
from tqdm import tqdm
import seaborn as sns
import multiprocessing as mp
import fnmatch
import pickle

#--Run Options--#
conf_dir = os.path.join(os.getcwd(), 'confs/')
output_dir = os.path.join(os.getcwd(), 'outputs/')


grid_dir_name = 'bursts_oscillation_fixed'
new_conf_dir = os.path.join(conf_dir, grid_dir_name)
new_output_dir = os.path.join(output_dir, grid_dir_name)


# Function to process each output file
def df_row_builder(output_file, df_dict):
    try:
        output = sp.dot_output(output_file)

        numerical = output.df(gains=False)
    #     numerical_normalize = output.df(gains=False, normalize = True)
        gains = output.df(gains=True)
        
        pre_gains = gains.loc[:output.stim_onset - 10].mean()
        post_gains = gains.loc[output.time - 10:output.time].mean() # grab average gain from last 10 seconds (post-stim) simulation

        row = post_gains
        row.name = output.f_name

        pre_stim = numerical.loc[:output.stim_onset - 10]
        post_stim = numerical.loc[output.stim_onset + output.stim_duration + 110:]
    
    except Exception as e:
        print(e)  # Print the exception message
        
        
    try:
        
        row['V_AUC_delta'] = sp.PSD_power_delta(
            pre_stim['pop.e.v'],
            post_stim['pop.e.v'],
            output.sampling_rate,
            bin_min = 1,
            bin_max = 50,
            normalize = False,
            fooof_correct=False
        )

        row['alpha_AUC_delta'] = sp.PSD_power_delta(
            pre_stim['pop.e.v'],
            post_stim['pop.e.v'],
            output.sampling_rate,
            bin_min = 8,
            bin_max = 13,
            normalize = True,
            fooof_correct=False
        )
        
        row['alpha_CF'] = float(sp.PSD(
            pre_stim['pop.e.v'],
            output.sampling_rate)[7:14].idxmax())

        row['FOOOF_AUC_delta'] = sp.PSD_power_delta(
            pre_stim['pop.e.v'],
            post_stim['pop.e.v'],
            output.sampling_rate,
            fooof_correct=True
        )
        
        nu_cols = [c for c in pre_stim.columns if fnmatch.fnmatch(c, 'coupling.*.nu')]
        pre_nu = pre_stim[nu_cols].mean()
        post_nu = post_stim[nu_cols].mean()
        nu_delta = abs((post_nu - pre_nu) / pre_nu)
        for idx, nu in nu_delta.iteritems():
            row[f'delta_{idx}'] = nu
            
        gains_delta = abs((post_gains - pre_gains) / pre_gains)
        for idx, gain in gains_delta.iteritems():
            row[f'delta_{idx}'] = gain

#         row['nu_ts'] = numerical_normalize[cols][output.stim_onset:output.stim_onset + output.stim_duration]
        
#         itbs = numerical['pop.x.q'][int(output.stim_onset):int(output.stim_onset + output.stim_duration)]
#         row['itbs'] = itbs.values
#         row['itbs_psd'] = sp.PSD(itbs, output.sampling_rate).values


        df_dict[row.name] = row

    except Exception as e:
        print(e)  # Print the exception message
        
        
def serialized_load(output_files):
    """
    Iteratively generate dataframe rows.
    """
    print('Serialized loading...')
    df_dict = {}
    for output_file in tqdm(output_files):
        df_dict[output_file] = df_row_builder(output_file, df_dict)
        
    return df_dict


# Function to parallelize the loading process
def parallel_load(output_files):
    """
    Use multiprocesses to parallelize generating dataframe rows.
    """
    print('Parallelized loading...')
    manager = mp.Manager()
    df_dict = manager.dict() # Dictionary that gets shared among the multiprocess

    # Create a process pool with the number of available CPU cores
    pool = mp.Pool() # 'processes' argument may be passed if loading hits memory limit

    # Use tqdm to track the progress of the parallel loading
    with tqdm(total=len(output_files)) as pbar:
        # Define a helper function to update the progress bar
        def update_pbar(_):
            pbar.update(1)

        # Apply the paralloader function to each output file in parallel
        for output_file in output_files:
            pool.apply_async(df_row_builder, args=(output_file, df_dict), callback=update_pbar)

        # Close the pool
        pool.close()
        pool.join()
    
    return df_dict


def perm_load(output_files, load_type = 'parallel'):
    """
    Load permuatations of .output files given a list of paths. 
    """
    
    if load_type == 'parallel':
        df_dict = parallel_load(output_files)
    elif load_type == 'serial':
        df_dict = serialized_load(output_files)
    else:
        raise Exception('load_type must be either "parallel" or "serial".')
        
    # Convert the dictionary, whose entries are rows of values, to a DataFrame
    xyz_gainer = pd.DataFrame.from_dict(df_dict, orient='index')

    # Extract parameter values contained within indicies and add each as a column value
    protocol_params = {i: sp.string_params(i) for i in xyz_gainer.index}
    for idx, param in protocol_params.items():
        for param_name, param_val in param.items():
            xyz_gainer.loc[idx, f'PARAM_{param_name}'] = float(param_val)

    num_params = len(next(iter(protocol_params.values())))
    xyz_gainer = xyz_gainer.sort_values(by = list(xyz_gainer.columns[-num_params:]), 
                                  ascending = [True] * num_params)
    
    
    return xyz_gainer

#### Normal load ####
# grid = sp.list_files(new_output_dir, full_path=True, extension_filter='.output')
# if len(grid) == 0:
#     raise Exception('Directory path contains no files.')
# with open('real_phys_idx.pickle', 'rb') as file:
#     real_phys_idx = pickle.load(file)
# grid_phys = [g for g in grid if os.path.basename(g) in list(real_phys_idx)]

# xyz_gainer = perm_load(grid_phys)




#### Tau load ####
# xyz_gain_dict = {}
# taus = [i for i in sorted(os.listdir(os.path.join(output_dir, 'tau_loop/'))) if '=' in i]

# for i in taus:
#     grid_dir_name = os.path.join(output_dir, 'tau_loop/', i)


#     grid = sp.list_files(grid_dir_name, full_path=True, extension_filter='.output')
#     xyz_gainer = perm_load(grid)
#     xyz_gain_dict[i] = xyz_gainer

#     print(i)
    

#### Dosage load ####
new_output_dir = [f'bursts_oscillation_{i}' for i in range(100, 1000, 20)]

    
xyz_gains_dict = {}
for i in new_output_dir:
    print(i)

    grid = sp.list_files(os.path.join(output_dir, i), full_path=True, extension_filter='.output')
    with open('real_phys_idx.pickle', 'rb') as file:
        real_phys_idx = pickle.load(file)
    grid_phys = [g for g in grid if os.path.basename(g) in list(real_phys_idx)]

    xyz_gainer = perm_load(grid_phys, load_type = 'parallel')
    xyz_gains_dict[i] = xyz_gainer
    
    
with open('xyz_gain_dict_100-980.pkl', 'wb') as file:
    pickle.dump(xyz_gains_dict, file)