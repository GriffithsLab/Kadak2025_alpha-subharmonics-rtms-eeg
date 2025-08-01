import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import welch
from fooof import FOOOF
import traceback


class PSD:
    def __init__(self, signal, sampling_freq, normalize = False, 
                 bin_min = .2, 
                 bin_max = 50,
                 bins_per_freq = 2):
        """
        Power spectrum class object.  Given frequency bin and power value arrays, returns a PSD dataframe when called (ie. sp.PSD(args)()).
        
        Optionally set fooof = True (default: False) to fit the PSD and set the fitted model (fm) object as an attribute.
        """
        self.sampling_freq = sampling_freq
        nperseg = self.sampling_freq * bins_per_freq
        
        self.bins, self.power = welch(signal.values.reshape(len(signal)),
                                      fs = self.sampling_freq, 
                                      nperseg = nperseg)
        
        if len(self.bins) == 0:
            raise Exception('Problem with computing PSD; bins/power is empty.  Check the passed signal.')
            
        
        welch_df = pd.DataFrame({'power': self.power}, index = self.bins) # power value at each frequency biny
        welch_df.index.names = ['bins'] # frequency bins
        
        self.psd = welch_df.loc[bin_min:bin_max]
        self.bins = self.psd.index.values
        self.power = self.psd['power'].values
        
        if normalize:
            self.psd = self._normalize()
    
    def __call__(self):
        """
        When evoking sp.PSD(signal, sampling_freq)(), returns a pandas df with index as freq bins and column as power values.
        """
        return self.psd
    
    def _normalize(self):
        """
        Normalize the power spectra.
        """
        normalized_PSD = self.psd.copy()
        total_power = normalized_PSD['power'].sum()
        normalized_PSD['power'] = normalized_PSD['power'] / total_power

        return normalized_PSD
    
    def fm(self, aperiodic_mode = 'knee'):
        """
        Call the fooof class to fit a model with power and freq values; returns the fitted fm object containing fitted data.
        """
        fm_fooof = FOOOF_params(self.power, self.bins, aperiodic_mode) # Create FOOOF_params class object
        return fm_fooof() # Call class object, which returns its fitted model (fm)
    
    def fm_aperiodic_params(self, aper_param = 'all'):
        aper_param = aper_param.lower()
        
        if len(self.fm().aperiodic_params_) == 2:
            aper_columns = ['offset', 'exponent']
            if aper_param == 'knee':
                raise ValueError("fm was not fitted with a knee.")
        elif len(self.fm().aperiodic_params_) == 3:
            aper_columns = ['offset', 'knee', 'exponent']
            
            
        aper_df = pd.DataFrame(self.fm().aperiodic_params_, columns = aper_columns)
        
        if target_peak == 'all':
            return aper_df
        elif aper_param not in aper_columns:
            raise ValueError(f"'{aper_param}' not valid.  Pass either 'all' or one of ['offset', 'knee', 'exponent'].")

        return aper_df[aper_param]
    
    def fm_peak_params(self, target_peak = 'all', peak_param = 'all'):    
        peak_columns = ['CF', 'PW', 'BW']
        peaks_df = pd.DataFrame(self.fm().peak_params_, columns = peak_columns)
        
        if target_peak == 'all':
            return peaks_df
        elif isinstance(target_peak, list):
            peak_low_end, peak_high_end = target_peak
            if not len(target_peak) == 2 or peak_low_end > peak_high_end:
                raise ValueError('target_peak range must be passed in format [low_end, high_end].  low_end must be < high_end.')
            
            # Find the largest peak between a given frequency range of the PSD
            filtered_freqs = peaks_df[(peaks_df['CF'] >= peak_low_end) & (peaks_df['CF'] <= peak_high_end)]
            if filtered_freqs.empty:
                raise Exception(f'No peaks detected between {peak_low_end} and {peak_high_end} Hz.')
            largest_peak_idx = filtered_freqs['PW'].idxmax()
            target_row = peaks_df.iloc[largest_peak_idx]
            
        elif isinstance(target_peak, int):
            target_row = peaks_df.iloc[(peaks_df['CF'] - target_peak).abs().idxmin()] # Grab by peak nearest to target_peak integer
        else:
            raise ValueError('target_peak must be either "all", an integer, or a list with low and high_end ranges (ie. [8, 13]).')
        
        
        if peak_param == 'all':
            return target_row
        elif peak_param not in peak_columns:
            raise ValueError(f'peak_param must be one of: {peak_columns}')
        
        return target_row[peak_param]

    
class FOOOF_params:
    def __init__(self, power, bins, aperiodic_mode):
        self.power = np.array(power) # power values
        self.freqs = np.array(bins) # frequency bins
        self.aperiodic_mode = aperiodic_mode # see https://fooof-tools.github.io/fooof/auto_tutorials/plot_05-AperiodicFitting.html
        self.fm = self._fit_model() # fitted fooof model object
        
        if len(self.fm.peak_params_) == 0:
            raise Exception('FOOOF could not successfully fit a model to the provided spectra.')

    def __call__(self):
        return self.fm
    
    def _fit_model(self):
        """
        Given power value and frequency bins arrays, fit a PSD to a FOOOF object
        """
        bin_range = [min(self.freqs), max(self.freqs)] # freq range
        fm = FOOOF(aperiodic_mode = self.aperiodic_mode, verbose = False) # Define fooof object
        fm.fit(self.freqs, self.power, bin_range) # fit PSD model in fooof object; now contains attributes

        return fm

    
def PSD_delta(pre_signal, post_signal, sampling_freq, target_peak = 'broadband', peak_param = 'PW'):
    pre_psd = PSD(pre_signal, sampling_freq)
    post_psd = PSD(post_signal, sampling_freq)
    
    if target_peak == 'broadband':
        pre_psd = pre_psd() # call the class object to return the psd df
        post_psd = post_psd()

        pre_auc = np.trapz(pre_psd.values.flatten())
        post_auc = np.trapz(post_psd.values.flatten())
        
        AUC_delta = (pre_auc - post_auc) / pre_auc
    
        return AUC_delta
    
    elif isinstance(target_peak, int) or isinstance(target_peak, list): # PSD peak nearest to an inputted frequency bin
        pre_peak_param_value = float(pre_psd.fm_peak_params(target_peak, peak_param))
        post_peak_param_value = float(post_psd.fm_peak_params(target_peak, peak_param))
        
        FOOOF_delta = (pre_peak_param_value - post_peak_param_value) / pre_peak_param_value
        
        return FOOOF_delta
    
    else:
        raise ValueError('target_peak must be either equal to "broadband", an integer, or a list with low and high_end integers.')



# def graph_PSD_delta(pre_signal, 
#                     post_signal,
#                     sampling_freq, 
#                     normalize = False):
#     """
#     Argument:
#         eirs_grid multi-index dataframe
    
#     Plots interact_manual PSD graph for jupyter notebook
#     """
#     welch_df = pre_post_PSD(pre_signal, post_signal, sampling_freq, normalize)

#     psd_fig, psd_ax = plt.subplots(figsize = (20,10))

#     welch_df['pre_power'].plot(ax=psd_ax, logx = False, logy=True, c='black', label = 'Pre-stim Voltage', linewidth = 4, linestyle='--')
#     welch_df['post_power'].plot(ax=psd_ax,logx = False, logy=True, c='indigo', label = 'Post-stim Voltage', linewidth = 4)

#     psd_ax.axvspan(8, 
#         13, 
#         color = 'pink',
#         alpha = .5) 


#     plt.xticks(fontsize = 15)
#     plt.yticks(fontsize = 15)

#     psd_ax.set_ylabel('Spectral Power [$V^2$/Hz]', fontsize = 30)
#     psd_ax.set_xlabel('Frequencies [Hz]', fontsize = 30)
# #     psd_ax.set_title(f'Pre vs. Post Stimulation Population Voltage PSD | bur={ppb}, osc={osc}', fontsize = 30)
#     psd_ax.tick_params(axis='both', which='major', labelsize=20)
#     psd_ax.set_xscale('log', base = 10)

#     psd_ax.legend()
#     plt.show()