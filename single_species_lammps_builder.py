

import csv
import numpy as np
import random

def write_single_species_LammpsScript(Temperature,densities,zbars,masses,system_index_species,box,cutoff,Teq,Trun,index_species):
    
    """
        This script takes thermodynamical conditions of a plasma: temperature, densities, ionisation state (zbars), masses, together with the number of
        "of elements in the system, simulation box and cutoff sizes [in units of Wigner-Seitz radius], equilibration and production number steps, to generate a LAMMPS script file.
        
        Author: Abdou Diaw
        """
    nspec=system_index_species
    for p in index_species:
        with open('lammpsScript_'+str(p)+str(p), 'w') as LammpsScript:
            
            
            # Once the zeros are removed estimte the number of species.
            #######################-----------------------------------------------#######################
            ## Estimate here parameters needed for the forces: screening length, force cutoff,
            ## time step, and drag frequency for thermostat.
            
            kb=       1.3807e-23
            hbar2=        1.1121811600000002e-68
            emass= 9.1094e-31
            eps0=8.8542e-12
            echarge= 1.6022e-19
            
            edens = 1.e6*sum(zbars*densities)
            Ef    = hbar2*(3.*np.pi**2*edens)**(2/3)/(2*emass)
            Debye = np.sqrt(eps0*np.sqrt((kb*Temperature*11600)**2+(2.*Ef/3)**2)/(edens*echarge*echarge))
            scnlng =  1./Debye
            aws=(3./(4*np.pi*sum(1.e6*densities)))**(1./3.)
            rc=cutoff*aws
            dbin=0.1*rc
            Temp1=Temperature*11600
            Z_av=       sum(zbars*densities/sum(densities))
            m_av=       sum(densities*masses/sum(densities))
            omega_p=    np.sqrt((echarge*Z_av)**2*sum(1.e6*densities)/(eps0*1.e-3*m_av))
            dtstep =    1./(100.*omega_p)
            Tdamp  =    1.e2*dtstep
            
            # Simulations box and particles number
            
            l=box*aws
            volume =l**3
            N=[]
            for s in range(len(densities)):
                N.append(int(volume*1.e6*densities[s]))
        
        
            #######################-----------------------------------------------#######################
            
            # Use the above quantities to build a LAMMPS script
        
            csv_writer = csv.writer(LammpsScript,delimiter=' ',quoting=csv.QUOTE_NONE,quotechar="'",doublequote=True)
            csv_writer.writerow(['#', 'LAMMPS', 'script'])
            csv_writer.writerow('')
            csv_writer.writerow(['echo', 'both'])
            csv_writer.writerow('')
            
            csv_writer.writerow(['#############','Problem', 'setup','#############'])
            csv_writer.writerow('')
            csv_writer.writerow('')
            csv_writer.writerow(['units', 'si'])
            csv_writer.writerow(['boundary', 'p', 'p', 'p'])
            csv_writer.writerow(['atom_style', 'atomic'])
            csv_writer.writerow(['newton', 'on'])
            
            csv_writer.writerow('')
            csv_writer.writerow(['#############','Simulation', 'box','#############'])
            csv_writer.writerow('')
            csv_writer.writerow(['region', 'boxid', 'block',  0,  l, 0, l, 0, l])
            csv_writer.writerow(['create_box', len(densities), 'boxid'])
            
            seed =random.sample(range(10582, 105820), len(densities))
            for s in range(len(densities)):
                csv_writer.writerow(['create_atoms', s+1, 'random',  N[s], seed[s],'boxid'])
            
            csv_writer.writerow('')
            for s in range(len(densities)):
                csv_writer.writerow(['group','atom'+str(s+1),'type',s+1])


            csv_writer.writerow('')
            for s in range(len(densities)):
                csv_writer.writerow(['mass',s+1,masses[s]])
                csv_writer.writerow('')
                csv_writer.writerow(['#############','Interactions', 'screening-Coulomb','potentials', 'and',  'Neighbor', 'list','#############'])

                csv_writer.writerow('')
                csv_writer.writerow(['pair_style',  'yukawa', scnlng, rc])

                csv_writer.writerow('')
                nspecies=np.arange(1,len(densities)+1,1)

                csv_writer.writerow(['pair_coeff',1,1,2.5077244112372143e-28*zbars[0]*zbars[0]])

                for s in nspecies:
                    for j in nspecies[1:]:
                        if (s-j)!=1 and  (s-j) !=2:
                            csv_writer.writerow(['pair_coeff',s,j,2.5077244112372143e-28*zbars[s-1]*zbars[j-1]])

                csv_writer.writerow('')
                csv_writer.writerow(['neigh_modify','delay', '0','every', '1',  'check', 'yes','page','500000', 'one', '50000'])
                csv_writer.writerow(['neighbor', dbin,'bin'])

                csv_writer.writerow('')
                seed=78487
                csv_writer.writerow(['velocity','all', 'create',Temp1, seed,  'dist',  'gaussian'])
                csv_writer.writerow(['timestep',dtstep])

                csv_writer.writerow('')
                csv_writer.writerow(['#---------','Equilibration', 'using', 'Nose-Hoover', 'to', 'maintain', 'temperature','---------#'])

                csv_writer.writerow('')
                csv_writer.writerow(['fix','NVT1', 'all','nvt', 'temp', Temp1, Temp1,Tdamp])
                csv_writer.writerow('')
                csv_writer.writerow(['thermo_style','custom', 'step','temp', 'pe', 'ke','etotal'])
                csv_writer.writerow(['thermo',int(Teq/100)])
                csv_writer.writerow(['run',Teq])

                csv_writer.writerow('')

                csv_writer.writerow(['velocity','all', 'scale', Temp1])
                csv_writer.writerow(['#---------','Remove', 'the', 'thermostat','---------#'])
                csv_writer.writerow(['unfix','NVT1'])
                csv_writer.writerow(['reset_timestep','0'])
                csv_writer.writerow('')
                csv_writer.writerow(['#---------','Production', 'run', 'NVE', 'ensemble','---------#'])
                csv_writer.writerow('')
                csv_writer.writerow(['fix','NVE', 'all','nve'])

                csv_writer.writerow('')
                csv_writer.writerow(['#---------','Compute','correlation', 'functions', 'and', 'integrals','over', 'time','---------#'])


                row_list=['thermo_style','custom', 'step','temp', 'pe', 'ke','etotal']

                csv_writer.writerow('')
                for s in range(len(densities)):
                    csv_writer.writerow(['compute','vacf'+str(index_species[s]),'atom'+str(s+1),'vacf'])
                    csv_writer.writerow(['fix',str(s+1),'atom'+str(s+1),'vector','1', 'c_vacf'+str(index_species[s])+'[4]'])
                    csv_writer.writerow(['variable','Diff_'+str(p)+str(p),'equal', '1.e4*dt*trap(f_'+str(s+1)+')'+'/3'])
                    row_list.append('c_vacf'+str(index_species[s])+'[4]')
                    csv_writer.writerow('')
                    csv_writer.writerow('')
                csv_writer.writerow(row_list)
                csv_writer.writerow('')

            csv_writer.writerow('')
            csv_writer.writerow(['#---------','Write','coefficients', 'output', 'file','---------#'])
            csv_writer.writerow('')
            csv_writer.writerow('')
            csv_writer.writerow(['run',Teq])
            csv_writer.writerow(['print','D=${Diff_'+str(p)+str(p)+'}','file','diffusion_coefficient_'+str(p)+str(p)+'.csv'])


#
#x=0.0001
#densities=np.array([1,0.5,0.01,2,0.00001,0.00001])*0.5e25
#masses=np.array([3.3210778e-24,3.3210778e-24,6.633365399999999e-23,6.633365399999999e-23,6.633365399999999e-23,6.633365399999999e-23])
#zbars=np.array([1,13,13,13,13,13])
#Temperature=100
#eps_traces =1.e-3
#
## MD parameters:
#box  = 80.
#cutoff=2.5
#Teq  = 100
#Trun = 100
#
## Find zeros in the densities
#species_with_zeros_densities_index=[]
#traces_elements_index =[]
#non_traces_elements_index=[]
#
#for i in range(len(densities)):
#    if densities[i]==0:
#        species_with_zeros_densities_index.append(i)
#    # Put a check here to make sure all the densities are not zeros. If that the case stop the simulations.
#    elif densities[i]/sum(densities) < eps_traces:
#        traces_elements_index.append(i)
#        ## Build individual script for the trace elements.
#        for s in traces_elements_index:
#            dens=np.array([densities[s]])
#            Z=np.array([zbars[s]])
#            m=np.array([masses[s]])
#            b='single_'+str(s)+str(s)
#            writeLammpsScript(Temperature,dens,Z,m,b,box,cutoff,Teq,Trun,traces_elements_index)
#    else:
#        non_traces_elements_index.append(i)

