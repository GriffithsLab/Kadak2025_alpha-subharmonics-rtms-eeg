# Overview

This repository contains the code and results for the manuscript "Alpha rhythm subharmonics underlie responsiveness to theta burst stimulation via calcium metaplasticity" by Kevin Kadak, Davide Momi, Zheng Wang, Sorenza P. Bastiaens, Mohammad P. Oveisi, Taha Morshedzadeh, Minarose Ismail, Jan Fousek, and John D. Griffiths ([https://doi.org/10.1371/journal.pcbi.1012926](https://doi.org/10.1101/2025.06.17.660153)).

## Folders
`code` contains the .py files for generating
`data` contains the data object storing the results data based on iTBS and IAF permutations, including heatmaps and distributions.
`notebooks` contains the .ipynb files for using SynPy visualizing the final results and figures.
`parameters` contains the .conf file for the initial/state variable parameters of the model simulations upon which iTBS and IAF permutations are generated.
`SynPy` is a copy of my custom Python library that wraps NFTsim and provides a toolkit for data analysis, found [here](https://github.com/GriffithsLab/SynPy).