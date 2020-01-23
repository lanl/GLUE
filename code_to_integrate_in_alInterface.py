import os
import numpy as np
import subprocess as sp
import zbar as z
import writeLammpsScript as w


# Path of lammps script and lmp exec
current_directory= '/Users/l304975/LAMMPS_BUILDER'
lmp='/Users/l304975/Downloads/lammps-22Aug18/src/lmp_mpi'

# MD parameters:
box  = 10.
cutoff=2.5
Teq  = 50000
Trun = 2000000

p_int=20000
s_int=10
d_int=s_int*p_int
eps_traces =1.e-3

# These are the inputs from BGK or estimated from BGK inputs.

LammpsDens=np.array([0,1])*0.5e25
LammpsCharges=np.array([1,18])
m=np.array([3.3210778e-24,6.633365399999999e-23,2])
LammpsTemperature=200

# Make a copy of the inputs
LammpsDens0=LammpsDens
LammpsCharges0=LammpsCharges
m0=m

# Finds zeros and trace elements in the densities, then builds LAMMPS scripts.

(species_with_zeros_LammpsDens_index, scriptFiles)=w.check_zeros_trace_elements(LammpsTemperature,LammpsDens,LammpsCharges,m,box,cutoff,Teq,Trun,s_int,p_int,d_int,eps_traces)

print(species_with_zeros_LammpsDens_index)
print(scriptFiles)


# This is basically going to be the main change to the current version of the alInterface.py

## Find all LAMMPS script, lammpsScript_*, on the directory. And run all all of them.
#
for file in os.listdir(current_directory):
    if file.startswith("lammpsScript_"):
        lammps_script = open(file)
        args=['mpirun','-np', '4',lmp]
        sp.Popen(args, stdin=lammps_script).wait()

## Collect data into to mutual_diffusion.ij.csv files. The previous point and this one have to be done sequentially.

w.write_output_coeff(LammpsDens0,species_with_zeros_LammpsDens_index)
