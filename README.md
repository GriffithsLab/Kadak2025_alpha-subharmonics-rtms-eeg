# Overview
This repository contains the code and results for the manuscript "Alpha rhythm subharmonics underlie responsiveness to theta burst stimulation via calcium metaplasticity" by Kevin Kadak, Davide Momi, Zheng Wang, Sorenza P. Bastiaens, Mohammad P. Oveisi, Taha Morshedzadeh, Minarose Ismail, Jan Fousek, and John D. Griffiths ([https://doi.org/10.1371/journal.pcbi.1012926](https://doi.org/10.1101/2025.06.17.660153)).

## Methodological workflow and neurophysiological model for examining iTBS-induced calcium-dependent metaplasticity effects on resting-state EEG circuitry.
**A)** Corticothalamic column underlying resting-state EEG activity and a **B)** 4-population corticothalamic neural population model of its circuitry, comprised of cortical excitatory pyramidal (_e_) and inhibitory interneuron (_i_) populations, and thalamic excitatory relay (_s_) and inhibitory reticular (_r_) nuclei populations.  **C)** Intermittent theta-burst stimulation (iTBS) protocols deliver voltage-spiking stimuli to excitatory cortical populations. Cyan and purple timeseries depict pre- and post-stimulation resting-state activity, respectively, altered by plasticity-induced circuit modifications.  **D)** Flowchart of Ca2+ scheme wherein post-synaptic depolarization and glutaminergic binding induce metaplastic NMDARs to open, enabling the influx of calcium to drive plasticity effects, with moderate and large concentrations driving LTD and LTP, respectively. Connection weight changes are immediately translated through signalled plasticity (a physiological analog of immediate, though functionally unrealized cell states) before manifesting as fully expressed functional modifications via altered $\nu$ values, following a signal transduction delay. In conjunction, NMDAR conductance is altered based on the prior weight dynamics, thereby mediating the next instance of calcium influx subsequent plasticity effect. The signaled ($\tilde{\nu}$; pink) and expressed ($\nu$; purple) synaptic weight over pre, active, and post-canonical iTBS are shown for the excitatory-excitatory ($ee$) connection.  Yellow and blue windows depict when modulated connection weight is relatively stronger and weaker than initial efficacy, respectively.

<img width="3378" height="1900" alt="image" src="https://github.com/user-attachments/assets/37ec746f-5e4f-4b0f-b299-e4e9ea6c3d0d" />

## rTMS-induced EEG power modulation and circuit weight change is enhanced by IAF-iTBS alignment.
**A)** Heatmap of iTBS-induced broadband power suppression (pre - post AUC $\Delta$) across parameter space (brighter = stronger suppression), with **B)** samples of power spectra prior to (cyan) and following (purple) stimulation, showing greater degrees of power modulation near alpha harmonic frequencies; green marks the canonical iTBS protocol.  **C)** Further simulations with slowing/accelerating the alpha-band frequency show that IAF-iTBS resonance leads to proportional shifts in the inter-burst frequency of the most effective protocols.  **D)** Broadband power change as a function of ARD (top-left), pulses-per-burst (bottom-left), inter-burst frequency (top-right), and pulse rate (bottom-right). Together these results support the premise that natural circuit frequency predicts the degree of iTBS-induced broadband power modulation.

<img width="2000" height="1125" alt="image" src="https://github.com/user-attachments/assets/d5c7bf00-1708-430a-b769-3f49ce329cda" />


## Folders
- `code` contains the .py files for generating the parameter file permutations, running the simulations, computing results, and storing their contents in a dataframe. 
- `data` contains the data object storing the results data based on iTBS and IAF permutations, including heatmaps and distributions.
- `notebooks` contains the .ipynb files for using SynPy visualizing the final results and figures.
- `parameters` contains the .conf file for the initial/state variable parameters of the model simulations upon which iTBS and IAF permutations are generated.
- `SynPy` is a copy of my custom Python library that wraps NFTsim and provides a toolkit for data analysis, found [here](https://github.com/GriffithsLab/SynPy).

## Files
Files are numbered in the order in which they are ran to generate, analyze, and visualize the results data.
- `1-using-nftsim-with-SynPy` provides a simple walkthrough of the SynPy toolkit which will be subsequently used for data generation and analysis.
- `2-construct_results_df` calls SynPy to generate permutations of parameter files, submit those files as Slurm batch jobs to be processed by NFTsim, then calls SynPy again to compute results for each permutation, and finally save these results in a Python dataframe.
- `3-results-stats-and-figs` indexes the dataframe results object for visualization and statistical analysis.
