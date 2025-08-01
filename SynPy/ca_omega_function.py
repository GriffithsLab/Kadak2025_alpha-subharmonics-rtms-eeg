import numpy as np
import pandas as pd
import math
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns

from scipy.optimize import fsolve
from scipy import signal
from scipy.signal import welch


def sigmoid(C, x):
    return 1 /(1 + np.exp(-C * x))

def B_sigmoid(glu,
              glu_0 = 200e-6,
              B_0 = 30e3):
  """
  Glutamate binding rate sigmoid function.

  glu - | Volume/concentration of glutamate
  glu_0 - (200e-6 M; Moles) | Threshold for glutamate binding
  B_0 - (30 μM^-1; Micromoles per second) | Inverse proportionality to the standard deviation of the strength of glutamate binding

  """
  return sigmoid(glu - glu_0, B_0)

def H_function(V,
              V_r = 195e-3,
              Mg_0 = 45.5e-3,
              H_0 = 62):
  """
  Voltage-dependance of NMDAR activation function.

  V_r - (195 mV; milivolts) | Nernst potential, Shouval et al. 2002a
  Mg_0 - (45.5 mV; milivolts) | Voltage contribution by extraceullar Magnesium, Shouval et al. 2002b
  H_0 - (62 V^-1; volts per second) | Slope of sigmoid; values taken from Shouval et al. 2002b
  """
  return (V_r - V) * sigmoid(V - Mg_0, H_0)




xyth = 1e-4 # 1/10**4
x_0 = y_0 = xyth

x = 2.3e-2 # 1/43.5
x_1 = x

y = 2e-2 # 1/50
y_1 = y

x_2 = y_2 = 4e7 # 40 μM^-1

theta_d = .25e-6 # μM
theta_p = .45e-6 # μM


def x_potentiation_rate(Ca,
                        x_0 = x_0,
                        x_1 = x_1,
                        x_2 = x_2,
                        theta_p = theta_p):
    """


    Ca - volume/concentration of calcium
    x_0 - plasticity threshold learning rate (s; seconds) | nftsim: xyth, xth
    x_1 - (s; seconds) | nftsim: x, ltp
    x_2 - (μM^-1; micromoles per second)
    theta_p - calcium concentration threshold to induce LTP (μM; micromoles) | nftsim: Pth
    """
    
    return x_0 + x_1 * sigmoid(Ca-theta_p, x_2)

def y_depression_rate(Ca,
                      y_0 = y_0,
                      y_1 = y_1,
                      y_2 = y_2,
                      theta_d = theta_d,
                      theta_p = theta_p):
    """


    Ca - volume/concentration of calcium
    y_0 - plasticity threshold learning rate (s; seconds) | nftsim: xyth, yth
    y_1 - (s; seconds) | nftsim: y, ltd
    y_2 - (μM^-1; micromoles per second)
    theta_d - calcium concentration threshold to induce LTD (μM; micromoles) | nftsim: Dth
    theta_p - calcium concentration threshold to induce LTP (μM; micromoles) | nftsim: Pth
    """

    return y_0 + y_1 * sigmoid(Ca - theta_d, y_2) - y_1 * sigmoid(Ca - theta_p, y_2)


def Ca_eta(Ca,
           x_0 = x_0,
           x_1 = x_1,
           x_2 = x_2,
           y_0 = y_0,
           y_1 = y_1,
           y_2 = y_2,
           theta_d = theta_d,
           theta_p = theta_p):

    return x_potentiation_rate(Ca, x_0, x_1, x_2, theta_p) + y_depression_rate(Ca, y_0, y_1, y_2, theta_d, theta_p)


def Ca_Omega(Ca,
             x_0 = x_0,
             x_1 = x_1,
             x_2 = x_2,
             y_0 = y_0,
             y_1 = y_1,
             y_2 = y_2,
             theta_d = theta_d,
             theta_p = theta_p):

    return x_potentiation_rate(Ca, x_0, x_1, x_2, theta_p) / Ca_eta(Ca, x_0, x_1, x_2, y_0, y_1, y_2, theta_d, theta_p)

Ca_Omega(.00001)


x_values = np.arange(0, .1e-5, .1e-7)
y_values = [Ca_Omega(x) for x in x_values]

# Plot the function
fig, ax = plt.subplots(figsize = (10, 5))
ax.plot(x_values, y_values, c = 'black', linewidth = 6)
ax.set_xlabel('Ca$^{2+}(\mu$M)', fontsize = 20)
ax.set_ylabel('$\Omega$', fontsize = 20)

colors = [(0, '#c6e3ff'), (0.5, '#f2f2f2'), (1, '#ffecbf')]
cmap = LinearSegmentedColormap.from_list('custom_cmap', colors)
for i in range(len(x_values) - 1):
    ax.axvspan(x_values[i], x_values[i + 1], color=cmap(y_values[i]), alpha=1)

ax.title('Calcium Control Function')
plt.tight_layout()