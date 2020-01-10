import os
import numpy as np
import random
import csv
import subprocess as sp
import zbar as z
import writeLammpsScript as w


# Path of lammps script and lmp exec
directory= '/Users/diaw/LAMMPS_BUILDER/'
lmp='/Users/diaw/Downloads/lammps-master/src/lmp_mpi'


# We take here the inputs parameters from the BGK.
densities=np.array([1, 1])*1e25
charges=np.array([1,18])
Temperature=100
masses=np.array([3.3210778e-24,6.633365399999999e-23])

# We will not run mixtures where the isotopic ratios of species is larger thant eps.
# Those species will be considered as trace elements and therefore will be run independently
# and then use the self-coefficient to build mutual diffusion

eps_traces =1.e-3

# Make a copy of the inputs
densities0=densities
masses0=masses
charges0=charges

# The physical parameters for the MD simulation:
# box is the the lenght of the simulation box in terms of the Wigner-Seitz radius
# cutoff is the forces cutt-off in terms of  the Wigner-Seitz radius
# Teq is the number of time steps for the equilibration run
# Trun is the number of time steps for the production run; that is after the equilibration period.
# s_int: correlation length; p_int: sample interval; d_int: dump interval

box  = 40.
cutoff=1.5
Teq  = 5000
Trun = 10000

s_int=200
p_int=10
d_int=s_int*p_int

# The BGK can sometimes send us a list of densities containing zeros.
# We have to remove these zeros

# Find the zeros in the densities from BGK
# Once we are done with the zeros, and remove them from the density list,
# we need to find the traces elements, built MD script for these elements, and then remove them from the density list.
# We build LAMMPS script for the remaining element(s)
# Finally, we ran all the LAMMPS script(s) in the deck and generate files containing all the coefficients: 
# For the four elements system: 
# 16 files for the mutual diffusion (diffusion_coefficient_ij.csv) where i is the index of the elements [0,1,2,3]. Keep in mind that ij=ji. 
# 4 files for the viscosities (viscosity_coefficient_ii.csv).
# 4 files for the thermal conducitivities (conducitivities_ii.csv).

species_with_zeros_densities_index=[]
traces_elements_index =[]
non_traces_elements_index=[]

for i in range(len(densities)):
    if densities[i]==0.0:
        species_with_zeros_densities_index.append(i)
    # Put a check here to make sure all the densities are not zeros. If that the case stop the simulations.
    elif densities[i]/sum(densities) < eps_traces:
        traces_elements_index.append(i)
    else:
        non_traces_elements_index.append(i)

### Build individual script for the trace elements.

for s in traces_elements_index:
    dens=np.array([densities[s]])
    Z=np.array([charges[s]])
    m=np.array([masses[s]])
    b='single_'+str(s)+str(s)
    w.write_LammpsScript(Temperature,dens,Z,m,b,box,cutoff,Teq,Trun,traces_elements_index,s_int,p_int,d_int)

### Build LAMMPS script for the non trace elements.

for s in non_traces_elements_index:
    N=len(non_traces_elements_index)
    if N==1:
        b='single_'+str(s)+str(s)
    elif N==2:
        b='mixture_'+str(non_traces_elements_index[0])+str(non_traces_elements_index[1])
    elif N==3:
        b.append('mixture_'+str(non_traces_elements_index[0])+str(non_traces_elements_index[1])+str(non_traces_elements_index[2]))
    elif N==4:
        b.append('mixture_'+str(non_traces_elements_index[0])+str(non_traces_elements_index[1])+str(non_traces_elements_index[2])+str(non_traces_elements_index[3]))
    else:
        print('We only have trace and/or zeros species')

# Generate LAMMPS script after removing zeros and trace elements

w.write_LammpsScript(Temperature,densities[non_traces_elements_index],charges[non_traces_elements_index],masses[non_traces_elements_index],b,box,cutoff,Teq,Trun,non_traces_elements_index,s_int,p_int,d_int)



### Run and collect data
### Find all the lammps script on deck and run them

for file in os.listdir(directory):
    if file.startswith("lammpsScript_"):
        lammps_script = open(file)
        args=['mpirun','-np', '6',lmp]
        sp.Popen(args, stdin=lammps_script).wait()


### Use the MD  output to build mutual_diffusion for trace and missing species. Darken.

concentrations= densities0/sum(densities0)
nspecies=np.arange(0,len(concentrations),1)

### Take all the self-diffusions values
### Also create viscosities files for the zero densities species
d_ii= []
for i in nspecies:
    for j in species_with_zeros_densities_index:
        with open('diffusion_coefficient_'+str(j)+str(i)+'.csv', 'w') as f:
             csv_writer = csv.writer(f,delimiter=' ')
             csv_writer.writerow(['D=',0.])
        if i==j:
           with open('viscosity_coefficient_'+str(i)+str(j)+'.csv', 'w') as f:
                csv_writer = csv.writer(f,delimiter=' ')
                csv_writer.writerow(['v=',0])

           with open('conductivities_coefficient_'+str(i)+str(j)+'.csv', 'w') as f:
                csv_writer = csv.writer(f,delimiter=' ')
                csv_writer.writerow(['k=',0])

    with open('diffusion_coefficient_'+str(i)+str(i)+'.csv', 'r') as f:
        inp = f.readlines()
        data=np.array([i.strip('D=').strip().split() for i in inp],dtype=float)
        d_ii.append(data[0][-1])

### Use the self-diffusions above with the species concentrations to build mutual diffusion with Darken and dump into files

for i in nspecies:
    for j in nspecies:
        if i!=j:
            with open('diffusion_coefficient_'+str(i)+str(j)+'.csv', 'w') as f:
                csv_writer = csv.writer(f,delimiter=' ')
                csv_writer.writerow(['D=',concentrations[i]*d_ii[j]+concentrations[j]* d_ii[i]])
