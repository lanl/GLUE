#!/bin/bash

W=50                           #pore width A
T=300                          #temperature K
CD=0.2                        #Currrent density (g/cc)


DIF=1.1 #this number can be decreased for better accuracy at the expense of more MD calls

lammps () {

mkdir $1_$2_$3 #make directory to run the simulation

cp input  $1_$2_$3 # copy the template to the directoy 
cp script $1_$2_$3 # copy the script to run the simulaiton job

cd $1_$2_$3        # enter the simulation directory

co=187.7142679 # conversion factor to convert the density (g/cc) to number of methane molecules 
nc=$(echo $1 $3 $co | awk '{printf "%.0f\n",$1*$2*$3}') # estimate the number of molecules based on the density, width and the conversion factor

sed -i -e "s/aaa/$1/g" input # define the width in the input template
sed -i -e "s/bbb/$2/g" input # define the temperature in the input template
sed -i -e "s/ccc/$nc/g" input # define the number of molecules in the input template

sbatch --wait script # submit the job and wait for it to be done 
CBD= awk 'NR==3{print $2}' density #current bulk density to be read from the density file
cd ..                # return back to the main directory
}


lammps $W $T $CD # run the simulation for the first time

while [$CBD le $rho_bulk_target] # iterate till you find a good match 
do

CD=$(echo $CD $DIF | awk '{printf "%.4f\n",$1*$2}') # increase the current density 
lammps $W $T $CD # run the job to estimate the bulk density corresponding to the new total density 
cd ..                # return back to the main directory
done 

cp $W_$T_$CD/density.profile .       #copy the final density profile to the main directory 
