# Training Data

This directory contains what are effectively input decks to generate training data to pre-seed the active learning with.

## ICF

Our training dataset comprises input parameter settings (temperature, species densities, and ionization states) and we use this to obtain the corresponding outputs from the molecular dynamic simulator, where the output is an array of viscosity, thermal conductivity, and diffusion coefficients. We constructed our dataset as a random subset of a Latin hypercube experiment design containing 1100 samples in the five-dimensional parameter space. In order to capture the expected conditions for our problem (ICF/MARBLE), we focus on plasma with Deuterieum and Argon densities in the range  `10<sup>21</sup> cm^<sup>-3</sup> <= n<sub>D</sub>,n<sub>Ar</sub> <= 10<sup>25</sup>cm<sup>-3</sup>`, a plasma temperature in the range `20 eV <= T <= 500 eV`. The ionization states of the different species are calculated from the sample points using a Thomas-Fermi prescription.

`bgk.csv` and `bgk_masses.csv` are input decks to guide the `GLUECode_Service` in generating these outputs.
