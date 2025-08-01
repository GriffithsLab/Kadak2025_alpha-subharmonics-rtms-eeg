import os
import numpy as np
import pandas as pd
from .nftsim_generator_FUNCTIONS import param_value
from utils.nftsim import NF

class dot_output:
    pop_nums = {
            1 : 'e', # excitatory
            2 : 'i', # inhibitory
            3 : 'r', # reticular
            4 : 's', # relay
            5 : 'n', # noise input
            6 : 'x'} # TMS

#     conn_mat = {
#             1 : 'ee', # excitatory onto itself
#             2 : 'ei', # to excitatory from inhibitory
#             3 : 'es', # to excitatory from relay
#             4 : 'ex', # to excitatory from tms
#             5 : 'ie', # to inhibitory from excitatory
#             6 : 'ii', # inhibitory onto itself
#             7 : 'is', # to inhibitory from relay
#             8 : 're', # to reticular from excitatory
#             9 : 'rs', # to reticular from relay
#             10 : 'se', # to relay from excitatory
#             11 : 'sr', # to relay from reticular    
#             12 : 'sn'} # to relay from noise input
    
    def __init__(self, output_path):
        self.output_path = os.path.abspath(output_path)
        self.f_name = os.path.basename(self.output_path)
        if self.f_name.split('.')[-1] == 'conf':
            raise Exception('dot_output does not manage .conf files.  Pass a .output file instead.') 
        
        self.params = self._output_params() # Parameter segment of file
        self.conn_mat = self._conn_mat() # Construct connection matrix
        
        self.time = float(param_value('Time', self.params)) # Length of simulation (s)
        self.dt = float(param_value('Deltat', self.params)) # Timestep (s)
        self.nodes = int(param_value('Nodes', self.params)) # Number of nodes (#)
        self.sampling_rate = 1 / float(param_value('Interval', self.params)) # Number of written datapoints per second of simulation
        self.write_start = float(param_value('Start', self.params)) # Time in simulation when data begins being written (s)
        
        tms_param_dict = { # .conf keyword : class variable name
        'Onset': 'stim_onset', # Time in the stimulation when TMS begins (s)
        'Duration': 'stim_duration', # Total length of stimulation (s)
        'Amplitude': 'stim_amplitude', # Stimulation amplitude of TMS pulses; BELIEVE THIS IS IN THE UNIT OF microvolts (μV)
        'Bursts': 'stim_pulses_per_burst', # Number of TBS pulses per burst (#)
        'Burst Frequency': 'stim_intra_burst_freq', # Frequency of pulses within a burst (Hz)
        'Oscillation Frequency': 'stim_inter_burst_freq' # Frequency of bursts per second (Hz)
        }

        for tms_param in tms_param_dict.keys(): # If the file has TMS in it, assign its parameters as attributes to the class
            try:
                param = float(param_value(tms_param, self.params))
                setattr(self, tms_param_dict[tms_param], round(param, 4))
            except Exception:
                pass
            
    def __call__(self):
        return self.params
        
    def _output_params(self):
        """
        Parses and returns the initial parameter segment of the output_path file.
        """
        params = [] # param list; each list value is a .output file line
        with open(self.output_path, 'r') as O: # open .output file
            line = O.readline() # read in initial line
            while not line.startswith('====='): # if the line does not begin with '=====' (which prefaces the data)
                params.append(line) # add the line to the param list
                line = O.readline() # move onto next line in file

        return params
    
    def _conn_mat(self):
        """
        Given the default or passed dictionary object outlining the population number -> identifying letter, generate
        the dictionary object for their connections with the 'receipt-sender' label.
        """
        
        try:
            matrix_idx  = [idx + 2 for idx, i in enumerate(self.params) if 'matrix:' in i] # index where connection matrix values begin
            if not len(matrix_idx) == 1:
                raise Exception('Either zero or multiple instances of "matrix:" present in parameters.  Cannot construct connection matrix.')

            matrix_idx = matrix_idx[0]
            string_conn_mat = self.params[matrix_idx : matrix_idx + len(self.pop_nums)] # make the range equal to the length of the pop dict

            matrix = [] # convert the string version of the conn_mat into a proper array
            for row_num, row in enumerate(string_conn_mat): # for each row
                row = row.split()[2:] # Exclude the row label and first column
                row = [int(num) if num.isdigit() else 0 for num in row]
                matrix.append(row)

            conn_mat = {}
            for row_num, row in enumerate(matrix): # for each row in the matrix (afferent population; To:)
                for col_num, col in enumerate(row):  # for each column in the trow (efferent population; From:)
                    if matrix[row_num][col_num]: # if there is a non-zero number (ie. a connection)
                        conn_mat[matrix[row_num][col_num]] = f'{self.pop_nums[row_num + 1]}{self.pop_nums[col_num + 1]}' # add to conn_mat dict

            return conn_mat
        
        except:
            return None
            
    def NFTsim_obj(self):
        """
        Returns the NFTsim output class object.
        """
        return NF(nf_output_file = self.output_path)

    def df(self, gains = False, normalize = False, _name_field_ = True):
        """
        Given a .output file path, constructs a dataframe object with each column representing a field (+ nodes) and an index of time.
        """
        Res = self.NFTsim_obj() # NFTsim output class object; calls the __call__ method of the present class

        field_dict = {}
        for field, node_ts in Res.data_dict.items(): # For each field and its nodes
            for node, data in node_ts.items(): # for each node and its timeseries
                if _name_field_: # Convert the field number to a population/connection letter
                    split_name = field.split('.') # split the string
                    if split_name[0] == 'pop': # if the field is a population (ie. Q, V; not a connection)
                        split_name[1] = self.pop_nums[int(split_name[1])] # grab the corresponding population label
                    else: # otherwise
                        split_name[1] = self.conn_mat[int(split_name[1])] # grab the corresponding connection matrix label

                    col_name = '.'.join(split_name) # construct the new name string
                else: 
                    col_name = field

                if self.nodes > 1: 
                    col_name = f"{col_name}_node.{node}"
                
                field_dict[col_name] = data
            
        field_df = pd.DataFrame(field_dict, index = Res.time + self.write_start)

        
        if normalize:
            field_df = (field_df - field_df.min()) / (field_df.max() - field_df.min())
       
    
        if gains: # only used for corticothalamic models
            alpha = float(param_value('alpha|Dendrite 1', self.params)) # rise rate of post-synaptic potential
            beta = float(param_value('beta|Dendrite 1', self.params)) # decay rate of post-synaptic potential
            Q_max = float(param_value('Qmax', self.params)) # population firing rate
            sigmoid_theta = float(param_value('Sigmoid Theta', self.params)) # mean population firing threshold, relative to rest
            sigma = float(param_value('Sigma|Firing', self.params)) # standard deviation of soma voltage, relative to threshold

            gain_dict = {}
            
            ct_connections = {k: v for k, v in self.conn_mat.items() if v not in {'ex', 'sn'}} # remove the non-synaptic connections
            for conn_num, conn_name in ct_connections.items():
                postsynaptic_pop_name = conn_name[0]  # from each connection, grab corresponding postsynaptic pop #

                gain_ab = field_df[f'coupling.{conn_name}.nu'] * (
                    (Q_max * np.exp(-(field_df[f'pop.{postsynaptic_pop_name}.v'] - sigmoid_theta)/sigma)) / 
                    (sigma * (1 + np.exp(-(field_df[f'pop.{postsynaptic_pop_name}.v'] - sigmoid_theta)/sigma))**2))

                gain_dict[conn_name] = gain_ab

            gain = pd.DataFrame(gain_dict)

            gain['g_ese'] = gain['es'] * gain['se'] #  Gese = GesGse,
            gain['g_esre'] = gain['es'] * gain['sr'] * gain['re'] # Gesre = GesGsrGre
            gain['g_srs'] = gain['sr'] * gain['rs'] #  Gsrs = GsrGrs

            gain['X'] = gain['ee'] / (1 - gain['ei']) # Cortical loop gain
            gain['Y'] = (gain['g_ese'] + gain['g_esre']) / ((1 - gain['g_srs'])*(1 - gain['ei'])) # Cortico-thalamic loop gain
            gain['Z'] = -gain['g_srs'] * ((alpha*beta) / (alpha+beta)**2) # Intrathalamic loop gain

            return gain

        return field_df

