# Import to load the necessary functions to begin using python helper functions for NFTsim
import os, sys
from .nftsim_setup import nftsim_setup

nftsim_setup() # Check if NFTsim exists in directory.  Optionally clone and compile if not. 
sys.path.append('nftsim/') # Add nftsim package to path
[os.makedirs(d, exist_ok = True) for d in ('confs/', 'outputs/')] # Make conf & output file directories (unless they already exist)

# Local functions; allows sp.FUNCTION commands to be made
from .nftsim_generator_FUNCTIONS import *
from .spectra_functions import *
from .conf_handler import *
from .output_handler import *
from .load import *
from .param_space import *