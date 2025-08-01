# Data & directory navigation
import os
import sys
import glob
import re
import subprocess


def norm(series):
    return (series - series.min()) / (series.max() - series.min())

def protocol_params(string):
    """
    Given a permutation string (ex. eirs-tms-custom_PERM_[bur=10.00_osc=1.75].output), returns a dicitonary of all protocol 
    parameters in the form {parameter-name: parameter value}.
    """
    # Extract the parameter sets using regex
    matches = re.findall(r'\[(.*?)\]', string)

    # Create an empty dictionary
    parameters = {}

    # Iterate over the matches and extract parameter names and values
    for match in matches:
        params = match.split('_')
        for param in params:
            param_name, param_value = param.split('=')
            parameters[param_name] = param_value

    return parameters


def tbs_pulse_amp(base_amp, pulses_per_burst, inter_burst_freq, amp_scale_factor=None, amp_scale_ceiling=None):
    """
    Calculate scaled pulse amplitude for TBS protocols.
    
    Args:
        base_amp: Base amplitude value
        pulses_per_burst: Number of pulses per burst
        inter_burst_freq: Frequency between bursts (Hz)
        amp_scale_factor: Optional factor to control scaling magnitude (0-1)
                         Lower values reduce the scaling effect
                         If None, full scaling is applied (equivalent to 1.0)
        amp_scale_ceiling: Maximum allowed amplitude multiplier
    
    Returns:
        Scaled amplitude value rounded to 2 decimal places
    """
    # Define the conventional iTBS parameters
    conventional_stim_intensity = tbs_train_dose(pulses_per_burst=3, 
                                                inter_burst_freq=5)
                
    # Calculate intensity for requested protocol
    protocol_stim_intensity = tbs_train_dose(pulses_per_burst=pulses_per_burst, 
                                           inter_burst_freq=inter_burst_freq)
    
    # Calculate the raw scaling ratio
    scaling_ratio = conventional_stim_intensity / protocol_stim_intensity
    
    # Apply scaling factor to moderate the adjustment if provided
    if amp_scale_factor is not None:
        adjusted_scaling_ratio = 1.0 + (scaling_ratio - 1.0) * amp_scale_factor
    else:
        adjusted_scaling_ratio = scaling_ratio
    
    # Apply the adjusted scaling ratio
    scaled_protocol_amplitude = base_amp * adjusted_scaling_ratio
    
    # Apply ceiling if provided
    if amp_scale_ceiling is not None: # was 2
        scaled_protocol_amplitude = min(scaled_protocol_amplitude, base_amp * amp_scale_ceiling)
    
    return format(scaled_protocol_amplitude, '.2f')


# def tbs_pulse_amp(base_amp, pulses_per_burst, inter_burst_freq, amp_scale_factor = , amp_scale_ceiling = None): # amp_scale_limit = 2
    
#     conventional_stim_intensity = tbs_train_dose(pulses_per_burst = 3, 
#                                                  inter_burst_freq = 5)
                                               
                
#     protocol_stim_intensity = tbs_train_dose(pulses_per_burst = pulses_per_burst, 
#                                             inter_burst_freq = inter_burst_freq)

#     scaled_protocol_amplitude = base_amp * (conventional_stim_intensity / protocol_stim_intensity)
    
#     if amp_scale_ceiling:
#         scaled_protocol_amplitude = min(scaled_protocol_amplitude, base_amp * amp_scale_ceiling)
    
#     return format(scaled_protocol_amplitude, '.2f')

def tbs_train_dose(pulses_per_burst, inter_burst_freq, on_time = 2, off_time = 8):
    return tbs_time_pulse(stim_length = on_time + off_time, 
                          pulses_per_burst = pulses_per_burst, 
                          inter_burst_freq = inter_burst_freq,
                          floor = False)

def tbs_pulse_time(num_pulses, pulses_per_burst = 3, inter_burst_freq = 5, on_time = 2, off_time = 8, floor = False):
    """
    Calculate the amount of time in seconds to administer num_pulses for theta burst stimulation.  
    
    Defaults to iTBS.  Set off_time = 0 for cTBS
    """
    
    # use floor division of train length if 'floor' passed
    return eval(f'num_pulses / ((pulses_per_burst*inter_burst_freq*on_time) {"//" if floor else "/"} (on_time + off_time))')


def tbs_time_pulse(stim_length, pulses_per_burst = 3, inter_burst_freq = 5, on_time = 2, off_time = 8, floor = False):
    """
    Calculate the amount of pulses that are administered with theta burst stimulation for a given stimulation length.  
    e.g. how many pulses come from 200 seconds of standard iTBS? returns 600
    
    
    Defaults to iTBS.  Set off_time = 0 for cTBS
    """
    
    # use floor division of train length if 'floor' passed
    return eval(f'stim_length * ((pulses_per_burst*inter_burst_freq*on_time) {"//" if floor else "/"} (on_time + off_time))')


# sys.path.append('nftsim/')
def nftsim_run(nftsim_path, conf_path, output_path):
    nftsim_shell_code = f'{nftsim_path} -i {conf_path} -o {output_path}'
    try:
        subprocess.run(nftsim_shell_code, shell=True, capture_output=True, check=True)
    except:
        try:
            subprocess.run('module load gcc/9.4.0 && ' + nftsim_shell_code, shell=True, capture_output=True, check=True)
        except subprocess.CalledProcessError as e: #'Errors may potentially be due to CPU environment permissions
            raise Exception('NFTsim could not run.  Subprocess error occurred:', e)

def _natural_sort_(string_list):
    """
    Given a list of strings, returns them in natural alphanumeric order.
    """
    
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)] 
    
    return sorted(string_list, key=alphanum_key)    


def list_files(file_dir, full_path = False, extension_filter = ''):
    """
    Given a directory containing multiple files, returns a sorted alphanumeric list of their name strings.
    
    Optional parameter: 
        full_path (default: False) may be set to True to return the absolute path string instead of only the file name.
    """
    if full_path:
        # returns list of absolute path strings
        return _natural_sort_([o for o in glob.glob(os.path.join(file_dir, '*')) if o.endswith(extension_filter)]) 
    else:
        # returns list of file name strings only
        return _natural_sort_([o for o in os.listdir(file_dir) if o.endswith(extension_filter)])


def tbs_train_dosage(pulses_per_burst, inter_burst_freq, on_time = 2, off_time = 8,):
    """
    Calculate the pulse dosage (number of administered pulses) per TBS train.
    """

    
    train_dosage = tbs_time_pulse(stim_length = on_time + off_time, 
                                  pulses_per_burst = pulses_per_burst,
                                  inter_burst_freq = inter_burst_freq)

    return train_dosage


def keyword_instances(keyword, conf_txt): # returns all present instances of a keyword in conf_txt (index & line content)
    """
    Given a keyword and list of text lines (conf_txt), returns all instances of the kw and the lines numbers in which they are present.
    """
    
    instances = {}
    for line_idx, line_contents in enumerate(conf_txt):
        kw_match = re.search(keyword + "(.+)", line_contents, re.IGNORECASE)
        if kw_match:
            instances[line_idx] = line_contents

    return instances


def param_value(kw, conf_txt, _include_idxs_ = False):
    """
    Arguments:
        Keyword (string)
        'keyword|keyword_filter'

    Given a keyword and a sometimes necessary keyword filter, returns the corresponding parameter value of the keyword.  The keyword
    filter isolates instances of the keyword to only the line(s) also containing the keyword filter.
    
    Returns:
        Corresponding parameter value
    """
    if '|' in kw:
        keyword, keyword_filter = kw.split('|')
    else:
        keyword = kw; keyword_filter = ''
    
    keyword = keyword.strip(':'); keyword_filter = keyword_filter.strip(':') # remove ';' from passed keyword strings

    # Dict of all keyword instances (line num : line content), filtered by instances not containing the keyword_filter
    kw_instances = {num: content for num, content in keyword_instances(keyword, conf_txt).items() 
                    if re.search(keyword_filter + "(:.+)", content, re.IGNORECASE)}
    
    if not kw_instances: # If there are no instances of the keyword in the conf_txt, raise error
        error_msg = f"No instances of '{keyword}' found"
        if keyword_filter != '': 
            error_msg += f" on lines containing '{keyword_filter}.  Try your keyword without the filter word.'"
        raise Exception(error_msg)

    elif len(kw_instances) == 1 or len(kw_instances) > 1 and len(set(kw_instances.values())) == 1: # If there's one instance, or multiple, equal instances of the keyword
        line_num = int(list(kw_instances.keys())[0]) # simply use the first instance
    
    else: # otherwise, request a line to select from the user
        for l, c in kw_instances.items(): # print each instance the keyword, then ask user to select the containing line
            print(f'{l, c}\n')
        line_num = int(input(f'{len(kw_instances)} instances of {keyword}. Select line number: '))

        
    # adds a space after ':' in any instances there is none, removes newline tag, and splits the conf_txt on spaces
    split_loi = re.sub(r'(?<=:)(?! )', ' ', conf_txt[line_num]).strip('\n').split(" ")
    
    kw = keyword.split(' ')
    for value_idx, value in enumerate(split_loi):
        value = value.strip(':')
        if len(kw) == 1 and re.match(keyword, value, re.IGNORECASE) or len(kw) == 2 and value_idx > 0 and \
            re.match(kw[0], split_loi[value_idx - 1], re.IGNORECASE) and \
            re.match(kw[1], value, re.IGNORECASE):

            for vplus_idx, vplus in enumerate(split_loi[value_idx:]):
                try:
                    float(vplus) # try converting the value at index vplus_idx after the index of the found kw to a float
                    if _include_idxs_:
                        return line_num, value_idx + vplus_idx, vplus # split loi index and value of corresponding kw
                    return vplus # by default, only return the corresponding keyword (parameter) value
                except:
                    continue # otherwise, jump to the next object in the split loi
                    
    return None


def _replace_value_(kw, new_value, conf_txt, verbose):
    """
    Given a keyword and keyword filter (used for multiple instances of the keyword in the conf_txt), replaces the corresponding 
    parameter (keyword) value with a new_value in the passed conf_txt object. 
    """
    new_value = str(new_value)
    if '|' in kw:
        keyword, keyword_filter = kw.split('|')
    else:
        keyword = kw; keyword_filter = ''
    
    line_num, value_idx, value = param_value(kw, conf_txt, _include_idxs_ = True)
    
    split_loi = re.sub(r'(?<=:)(?! )', ' ', conf_txt[line_num]).split(" ")
    if split_loi[value_idx] == split_loi[-1]: # if the kw is found at the last index (ie. end of the line)
        new_value += ('\n') # add a new line tag 
    
    split_loi[value_idx] = new_value # update the old value with the new at split line index vv
    conf_txt[line_num] = " ".join(split_loi) # re-combine the objects in split loi into a single, updated loi
    
    if verbose:
        print(f"Replacing {kw} '{value}' with '{new_value}' -- {conf_txt[line_num]}")
        
    conf_txt[:] = conf_txt # Update the conf_txt object in memory with the modified line
    
    
def update_param(keyword, new_value, conf_txt, verbose = True):
    _replace_value_(keyword, new_value, conf_txt, verbose)


def save_confs(new_confs, conf_dir = 'confs/'):
    """
    Takes a dictionary object containing a conf_string [key] and conf_content / conf_txt [value]
    
    Generate a new .conf file for each item in the passed new_confs dict
    """
    
    if not os.path.exists(conf_dir): # if the directory doesn't exist, create it
        os.makedirs(conf_dir)
    
    for conf_name, conf_contents in new_confs.items():
        open(os.path.join(conf_dir, conf_name), 'w+').writelines(conf_contents)

    print(f'Wrote {len(new_confs)} new conf files to: {conf_dir}')


# def quick_conf(f, conf_dir, output_dir, nft_path = 'nftsim/bin/nftsim', params = {}, gains = False, full_path_name = False, save_csv = False):
#     """
#     Given a .conf file, generates a .output file and returns its contents as a dataframe.
#     """
    
#     with open(f, 'r') as F:
#         conf_txt = F.readlines()
        
#     gen_file_string = str(f.split('.')[0]) + '_QUICK' # take the f name string, remove the '.conf', append tag
#     conf_name = gen_file_string + '.conf'
#     output_name = gen_file_string + '.output'
    
#     conf_path = os.path.join(conf_dir, conf_name)
#     output_path = os.path.join(output_dir, output_name)
    
#     # Update the value of each parameter within the passed 'params' dictionary, if the dict contains items
#     if params:
#         [update_param(kw, value, conf_txt) for kw, value in params.items()]
    
#     save_confs(
#        new_confs = {conf_name:conf_txt[:]},
#        conf_dir = conf_dir)
    
    
#     # Generate .output file from .conf file
#     nftsim_run(nftsim_path = nft_path, 
#                conf_path = conf_path, 
#                output_path = output_path)

#     df = output_to_df(output_path, gains = gains, full_path_name = full_path_name)

#     if save_csv: 
#         if not os.path.exists(os.getcwd() + '/csv/'): os.makedirs(os.getcwd() + '/csv/')
#         df.to_csv(f"/{os.getcwd()}/csv/{f.split('.')[0]}.csv")
    
#     print()
#     print(df)
    
#     return df


            
# def firing_lock_check(time_s, conf_txt, stim_onset, stim_duration, detect_threshold = .90):
#     print(f'time_s: {time_s}')
    
#     qmax = float(param_value('Qmax:', conf_txt)[1]) # Maximum firing rate allowed in the simulation
# #     stim_start_time =  float(param_value('Onset:', conf_txt, instance_guide = tms_type)[1]) # Time into simulation when stimulation begins being administered
#     stim_start_time = stim_onset
# #     stim_duration = float(param_value('Duration:', conf_txt)[1]) # Total time in seconds stimulation is administered
#     stim_duration = stim_duration
#     on_time = spike_length = int(param_value('On:', conf_txt)[1]) # Train interval; how long in seconds a spike occurs for; almost always proportional to ON time
#     off_time = int(param_value('Off:', conf_txt)[1]) # Inter-train interval
#     train_length = on_time + off_time # total time (s) of a stimulation ON + OFF cycle (1 full train)
#     num_spikes = int(stim_duration / train_length) # duration of stimulation / the stimulation incremenet in seconds
#     sampling_freq = 1 / float(param_value('Interval:', conf_txt)[1]) # in Hz
    
    
#     time_s = time_s.loc[stim_start_time : (stim_start_time + stim_duration)] # Trim the timeseries down to only the TMS ON portion
#     for spike in range(num_spikes): # for each spike in the total number of spikes that occur in the stim. time series:
#         spike_timing = (spike * train_length) # time (in seconds) in which a given spike first occurs
#         spike_idx = int(spike_timing * sampling_freq)  # positional index of when a spike first occurs
        

#         spike_firing_rate = time_s.iloc[spike_idx].values
#         bt_spike_firing_rate = min(time_s.iloc[int((spike_timing + spike_length) * sampling_freq) : int((spike_timing + train_length) * sampling_freq)].values)
        
#         if (detect_threshold * spike_firing_rate) < bt_spike_firing_rate and bt_spike_firing_rate > (detect_threshold * qmax):
#             return {spike: int((sampling_freq * stim_start_time) + (spike_idx - sampling_freq))}
    
#     return None


# def gen_ts_grid(f, conf_dir, output_dir, grid_type = 'ts'):
    
#     with open(f, 'r') as F: # read in template conf for param_value data
#         conf_txt = F.readlines()
        
#     con_num = param_value('Coupling:', conf_txt)[1]
    
#     ppb_size = 8
#     osc_size = 10

#     fig, ax = plt.subplots(figsize = (50, 30), 
#                            ncols = ppb_size, 
#                            nrows = osc_size)
    
#     sampling_freq =  1 / float(param_value('Interval:', conf_txt)[1])
#     stim_onset = float(param_value('Onset:', conf_txt, instance_guide = 'TBS')[1])
#     stim_duration = float(param_value('Duration:', conf_txt)[1])
#     on_time = float(param_value('On:', conf_txt)[1])
#     off_time = float(param_value('Off:', conf_txt)[1])
    
#     if grid_type == 'ts': grid_fields = [f'coupling.{con_num}.nutilde', f'coupling.{con_num}.nu']
#     elif grid_type == 'psd': grid_fields = [f'pop.{con_num}.v']

#     output_dicts = read_outputs(f, conf_dir, output_dir, grid_fields)

#     for output_name, output_dict in output_dicts.items(): # for output name (should be 80 objects)
#         ts_df = pd.DataFrame()
#         for field, ts in output_dict.items():
#             ts_df[field] = ts.iloc[:, 0]

#         print(ts_df)
#         ppb = output_name.split('ppb')[1].split('_')[0]
#         osc = output_name.split('osc')[1].split('_')[0]
#         print()
#         print(f'ppb: {ppb}')
#         print(f'osc: {osc}')

#         ax_item = ax[(osc_size - 1) - (int(osc) - 1), int(ppb) - 1]


#         if grid_type == 'ts':
#             ax_item.plot(ts_df)

#             num_pulses_given = 600
#             time600 = round(num_pulses_given*(on_time+off_time)/(int(osc)*int(ppb)*on_time), 2)
#             print(time600)
#             index_to_look = int(time600 + int(stim_onset))
#             ax_item.axvline(index_to_look, linestyle = '--', c = 'purple')


#             start_val = float(ts_df[f'coupling.{con_num}.nutilde'].iloc[0])

#             if index_to_look > float(ts_df[f'coupling.{con_num}.nutilde'].index[-1]): end_val = None
#             else: end_val = float(ts_df[f'coupling.{con_num}.nutilde'].loc[index_to_look])               


#             if end_val == None:
#                 diff = 'Out of range'
#             else: 
#                 diff = f'{(end_val - start_val) / start_val:.2%}'

#             ax_item.text(600, start_val, diff)
#             print(diff)
            
#         elif grid_type == 'psd':
#             ## WHEN forwarding a ts for psd plotting, make sure the specific column is grabbed, not the entire df that contains 1 column
#             voltage = ts_df[f'pop.{con_num}.v']

#             ts_pre_stim = voltage[:int(stim_onset)]
#             ts_post_stim = voltage[int(stim_onset) + int(stim_duration) + 5:]


#             for window, clr in zip([ts_pre_stim, ts_post_stim], ['dodgerblue', 'blueviolet']):
#                 valu = np.array(window)
#                 freqs, mypsd = welch(valu, fs = sampling_freq)
                
#                 ax_item.plot(freqs, mypsd, color = clr)

#             ax_item.set_xscale('log')
#             ax_item.set_yscale('log')
                
#         ax_item.set_title(f'Pulses/Burst: {ppb}, Theta: {osc} Hz')

#     plt.tight_layout()

#     if not os.path.exists(os.getcwd() + '/grids/'):
#         os.makedirs(os.getcwd() + '/grids/')

#     plt.savefig(os.getcwd() + '/grids/' + f.split('.')[0] + f'_{grid_type}_grid.png')