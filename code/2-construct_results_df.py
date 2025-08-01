# Author: Kevin Kadak

# This script generates a .pkl file containing a dataframe of all results.  
# This involves generating permutations of .conf (parameter) files that varying over iTBS parameter space
# This script will use an default parameter file (eirs-tms-custom.conf) as a template, then vary the approporiate values
# Upon generating each unique .conf file, it will submit HPC Slurm batch jobs to compute respective .output files via NFTsim
# Finally, upon the jobs finishing and writing the .output files to disk, the results data for each permutation will be grabbed and stored within a centralized data frame, which we save to the .pkl for later reading

# import necessary items
import os
os.environ['OMP_NUM_THREADS'] = '1' # os and this line need to be imported before *any* other packages, including SynPy
import SynPy as sp # this is the library containing Kevin Kadak's Python wrapper for NFTsim
import numpy as np
import time
import pickle
import shutil

#--Run Options--#
conf_dir = os.path.join(os.getcwd(), 'confs/dosage/')
output_dir = os.path.join(os.getcwd(), 'outputs/dosage/')

pkl = "scaled_amp_105_limit_with_gnmda.pkl" # name can be changed

pulse_dose_range = {'start' : 600, # for looping through various pulses doses.  Here, we only look at results after 600 pulses
                    'stop' : 600,
                    'step' : 20}




purge_dir = True #  If true, delete the conf and output files after the results df is generated and saved
purge_dict = True # If true, delete an existing pkl results file for generating a new one


def check_and_create_pkl(pkl_filename):
    """
    Check if a pickle file exists in the current working directory.
    If it does not exist, create a new pickle file with an empty dictionary.
    """
    if not os.path.isfile(pkl_filename):
        with open(pkl_filename, 'wb') as file:
            pickle.dump({}, file)





check_and_create_pkl(pkl)
if purge_dict:
    with open(pkl, 'wb') as file:
        pickle.dump({}, file)
with open(pkl, 'rb') as file:
    pickle.load(file)

        


for dose in range(pulse_dose_range['start'], 
                  pulse_dose_range['stop'] + pulse_dose_range['step'], 
                  pulse_dose_range['step']):
    
    grid_dir_name = f'bursts_oscillation_{dose}'
    new_conf_dir = os.path.join(conf_dir, grid_dir_name)
    new_output_dir = os.path.join(output_dir, grid_dir_name)

    # Run 
    params = { # Replaces each dictionary key with the corresponding value in the .conf
        'Onset:': 150,
    }

    perm_dict = { # Defines the parameter range to span, for each parameter
        'Bursts' : [2,20,1], # Ie. simulate unique outputs for rTMS with 2 to 20 pulses per burst, iterating by 1 burst per simulation
        'Oscillation Frequency' : [1,20,.25], # simulate unique outputs for rTMS with 1 to 20 inter-burst frequency, iterating by 0.25 Hz per simulation
    }
    
    expected_file_count = len(sp.valid_iTBS_protocols()) # To avoid simulating parameter combinations in non-physiological ranges
    
    def submit_jobs():
        
        if purge_dir:
            if os.path.exists(new_conf_dir):
                try:
                    shutil.rmtree(new_conf_dir)
                except: pass
            if os.path.exists(new_output_dir):
                try:
                    shutil.rmtree(new_output_dir)
                except: pass
                

        # Make the confs and submit them for batch jobs
        num_submitted_jobs = sp.dot_conf('eirs-tms-custom.conf').grid_outputs(perm_dict, # stores the number of submitted jobs to check and verify that we capture all outputs
                                                         new_conf_dir, 
                                                         new_output_dir, 
                                                         params, 
                                                         fixed_dose = dose,
                                                         dynamic_amp = 105, # this value is the amplitude for standard iTBS upon which other protocols will be scaled (selected because it compels clean ee nutilde signal oscillations during across stimulation, ala Fung and Robinson, 2014)
                                                         filtered_perms = True)


        while True: # continuely check which jobs are done, and when they've been successfully written to disk (to avoid race conditions; want to avoid loading and processing data before the data is finished being written to disk, even if the batch job for it is complete)
            complete_jobs = sp.list_files(new_output_dir, extension_filter = "done.txt")
            complete_output_files = sp.list_files(new_output_dir, extension_filter = ".output")

            if len(complete_jobs) >= num_submitted_jobs:
                break
            else:
                print(f'{len(complete_output_files)}/{expected_file_count} .output files written', end='; ') 
                print(f'{len(complete_jobs)}/{num_submitted_jobs} jobs fully complete')
                time.sleep(10)
    
    def load_outputs():

        with open(pkl, 'rb') as file:
            xyz_gain_dict = pickle.load(file)

        df = sp.perm_load(new_output_dir).perm_df(load_type = 'parallel')

        print(df)

        xyz_gain_dict[grid_dir_name] = df

        # Open the same file in binary write mode to save the modified data
        with open(pkl, 'wb') as file:
            pickle.dump(xyz_gain_dict, file)

        if len(df.index) != expected_file_count:
            missing_entries = [entry for entry in sp.valid_iTBS_protocols() if entry not in df.index]
            raise Exception(f'Write error; missing protocol entries: \n{missing_entries}')
            
    submit_jobs()
    load_outputs()
        
#     shutil.rmtree(new_conf_dir) # upon saving the results data, purge the conf files
#     shutil.rmtree(new_output_dir) # ^and the output files