import os
import numpy as np
from itertools import product
from .nftsim_generator_FUNCTIONS import (
    param_value, 
    update_param,
    tbs_pulse_amp,
    tbs_pulse_time,
    save_confs, 
    nftsim_run,
    protocol_params
)
from .output_handler import dot_output
from .batch_jobs import gen_outputs
from .param_space import valid_iTBS_protocols

class dot_conf:
    def __init__(self, conf_path):
        self.conf_path = os.path.abspath(conf_path)
        self.f_name = os.path.basename(self.conf_path)
        if self.f_name.split('.')[-1] == 'output':
            raise Exception('dot_conf does not manage .output files.  Pass a .conf file instead.') 
        
        with open(self.conf_path, 'r') as f:
            self.conf_text = f.readlines()
            
            
    def generate_permutations(self, loop_dict):
        """
        Takes a dictionary object with the name of the parameter being manipulated as the key, and the [start, stop, stepsize] list
        as the corresponding value.
        Ex.
        {'ppb': [1, 20, .25],
         'osc': [1, 20, .25],
         'amp': [70, 120, 5]}


        Returns a list containing tuple objects of each unique permutation.
        Ex.
        [(1, 1.0, 70),
         (1, 1.0, 75),
         (1, 1.0, 80),
         ...]
        """
        # Generate a list of loop ranges
        loop_ranges = [np.arange(start, stop + step, step) for loop_name, [start, stop, step] in loop_dict.items()]

        # Use the product function from the itertools module
        # to generate all permutations of the loop ranges
        perm_list = product(*loop_ranges)

        # Capture each unique permutation in a list
        all_permutations =  [perm for perm in perm_list]

        # Return all unique permutations
        return all_permutations


    def gen_confs(self, perm_dict, new_conf_dir, params = {}, 
                  fixed_dose = None,
                  dynamic_amp = None,
                  filtered_perms = True, 
                  write_confs = True, 
                  verbose = True):
        """
        perm_dict -- Dictionary object containing n parameters and their corresponding value ranges to generate permuations for.
                     Formatted as {'PARAMETER NAME' : [LOWEST VALUE, HIGHEST VALUE, STEP SIZE]}
                     
        new_conf_dir -- Directory to write the .conf permutations to.  Will create the directory if it does not exist.
        
        params (optional) -- Dictionary object to modify base parameters.
                             Formatted as {'PARAMETER NAME' : NEW VALUE}
                             
        write_confs -- True/False write permutations to disk.  Useful for first checking if permutations look correct before creating files
        
        Given a template .conf file and a dictionary object containing parameter values ranges to be iterated upon, 
        generates a new .conf for each unique permutation of parameters.  Writes each .conf file to disk by default.
        """

        new_conf_text = self.conf_text
        if params:
            [update_param(kw, value, new_conf_text, verbose) for kw, value in params.items()] # Alter base params before perms

        new_confs = {} # will take the format {f_name : conf_txt}

        perms = self.generate_permutations(perm_dict) # list of all unique parameter permutations from perm_dict
        keywords = list(perm_dict.keys())
        
        if filtered_perms: # Only generates confs based on if the parameter combination is present within the valid_iTBS_protocols set
            valid_param_combos = [tuple(map(float, p_combo)) for p_combo in (protocol_params(p).values() for p in valid_iTBS_protocols())]
            perms = [filtered_perm for filtered_perm in perms if filtered_perm in valid_param_combos]

        for perm in perms:

            # update the new_conf_text with each param in the unique permuatation item
            [update_param(keywords[p_idx], format(param, '.2f'), new_conf_text, verbose) for p_idx, param in enumerate(perm)]
            ### Adjusts stim length based on desired number of pulses ###
            if fixed_dose:
                stim_len = tbs_pulse_time(fixed_dose, 
                                          pulses_per_burst = float(param_value('Bursts', new_conf_text)), 
                                          inter_burst_freq = float(param_value('Oscillation Frequency', new_conf_text)))
                update_param('Duration', format(stim_len, '.2f'), new_conf_text, verbose)
                
                onset = float(param_value('Onset', new_conf_text))
                SIGNAL_TRANSDUCTION_DELAY = 100
                sim_len = onset + stim_len + SIGNAL_TRANSDUCTION_DELAY + onset # + 200 # old: onset + stim_len + SIGNAL_TRANSDUCTION_DELAY + onset
                update_param('Time', format(sim_len, '.2f'), new_conf_text, verbose)
                
            if dynamic_amp:
                update_param('Amplitude', tbs_pulse_amp(base_amp = dynamic_amp['standard_amp'], 
                                                        pulses_per_burst = float(param_value('Bursts', new_conf_text)), 
                                                        inter_burst_freq = float(param_value('Oscillation Frequency', new_conf_text)),
                                                        amp_scale_factor=dynamic_amp['scaling_factor'],
                                                        amp_scale_ceiling = 2), 
                             new_conf_text, verbose)
                
            #############################################################
                
            var_time = float(param_value('Time', new_conf_text))
            var_onset = float(param_value('Onset', new_conf_text))
            var_duration = float(param_value('Duration', new_conf_text))

            if var_time < (var_onset + var_duration): # Check that the stim onset + duration does not exceed the total simulation length
                raise ValueError('Parameter error: Stimulation onset + duration length > simulation length (time).') # Halt the process

             # list of key: param_value pair, per perm
            idv_params = [f'{key[:3]}={perm[k_idx]:.2f}' for k_idx, key in enumerate(keywords)]

            param_string = '_'.join(idv_params) # join them into one string, separated by '_' 
            perm_string = f"{str(self.f_name.split('.')[0])}_{'PERM'}_[{param_string.lower()}].conf" # full string for a given permuatation

            # make dictionary perm_string [key] correspond to the new_conf_text contents with all parameter changes of the permutation
            new_confs[perm_string] = new_conf_text[:]

        # Names the dir for the new confs based on perm_dict keys
        new_confs_dir_string = f'{"_".join([k.lower() for k in perm_dict.keys()])}/'.replace(':', '')
        
        if write_confs:
            save_confs(new_confs, new_conf_dir)

        return len(new_confs)
    
    
    def grid_outputs(self, perm_dict, new_conf_dir, new_output_dir, params = {}, 
                     
                     fixed_dose = None,
                     dynamic_amp = None,
                     filtered_perms = True,
                     batch = True,
                     nft_path = 'nftsim/bin/nftsim'):
        """
        Given a conf file path, a permutation dictionary, and new conf/output directory names, creates and writes each permutation 
        of the .conf file, then generates each corresponding .output file.
        
        perm_dict -- Dictionary object containing n parameters and their corresponding value ranges to generate permuations for.
                     Formatted as {'PARAMETER NAME' : [LOWEST VALUE, HIGHEST VALUE, STEP SIZE]}
                     
        new_conf_dir -- Directory to write the .conf permutations to.  Will create the directory if it does not exist.
        
        new_output_dir -- Directory to write the corresponding .output permutations to.  Will create the directory if it does not exist.
        
        params (optional) -- Dictionary object to modify base parameters.
                             Formatted as {'PARAMETER NAME' : NEW VALUE}
                             
        batch (optional; default: True):
            If True, submits jobs to process .conf files into .outputs through sbatch SLURM scheduler.
            If False, individually processes each .conf file through NFTsim.
        """

        grid_points = self.gen_confs(perm_dict, 
                                     new_conf_dir, 
                                     params, 
                                     fixed_dose,
                                     dynamic_amp,
                                     filtered_perms, 
                                     write_confs = True, 
                                     verbose = False)

        num_submitted_jobs = gen_outputs(new_conf_dir, 
                                         new_output_dir, 
                                         batch, 
                                         nft_path)

        print('Jobs submitted.')
        
        return num_submitted_jobs
                
    def run(self, conf_dir = 'confs/', output_dir = 'outputs/', params = {},
            gains = False, # return CT gain values instead of individual fields
            normalize = False, # return df with normalized column values
            _name_field_ = True, # alter column (field) names to replace numbers with letters
            nftsim_path = 'nftsim/bin/nftsim'):
        
        
        output_name = self.f_name.replace('.conf', '.output')
        output_path = os.path.join(output_dir, output_name)

        # Update the value of each parameter within the passed 'params' dictionary, if the dict contains items
        new_conf_text = self.conf_text
        
        if params:
            [update_param(kw, value, new_conf_text) for kw, value in params.items()]
        
        # Save a new .conf file, which may or may not have been modified by params, from which to generate the .output file
        save_confs(new_confs = {self.f_name: new_conf_text[:]},
                   conf_dir = conf_dir)

        # Generate .output file from .conf file
        nftsim_run(nftsim_path = nftsim_path, 
                   conf_path = os.path.join(conf_dir, self.f_name), 
                   output_path = output_path)

        return dot_output(output_path).df(gains, normalize, _name_field_)