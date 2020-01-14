import os
import numpy as np
import csv
import subprocess as sp
import zbar as z
import writeLammpsScript as w


# Path of lammps script and lmp exec
directory= '/Users/diaw/LAMMPS_BUILDER/'
lmp='/Users/diaw/Downloads/lammps-master/src/lmp_mpi'

# These are the inputs from BGK or estimated from BGK inputs.

LammpsDens=np.array([1,0])*0.5e25
masses=np.array([3.3210778e-24,6.633365399999999e-23])
LammpsCharges=np.array([1,13])
LammpsTemperature=200

# Trace elements
eps_traces =1.e-3

# Make a copy of the inputs
LammpsDens0=LammpsDens
masses0=masses
LammpsCharges0=LammpsCharges

# MD parameters:
box  = 20.
cutoff=1.
Teq  = 1000
Trun = 20000

p_int=200
s_int=10
d_int=s_int*p_int

# Finds zeros and trace elements in the densities, then builds LAMMPS scripts.

species_with_zeros_LammpsDens_index=w.check_zeros_trace_elements(LammpsTemperature,LammpsDens,LammpsCharges,masses,box,cutoff,Teq,Trun,s_int,p_int,d_int,eps_traces)

# Runs all LAMMPS script on directory

for file in os.listdir(directory):
    if file.startswith("lammpsScript_"):
        lammps_script = open(file)
        args=['mpirun','-np', '6',lmp]
        sp.Popen(args, stdin=lammps_script).wait()

# Collect data into to mutual_diffusion.ij.csv files. The previous point and this one have to be done sequentially.

w.write_output_coeff(LammpsDens0,species_with_zeros_LammpsDens_index)

