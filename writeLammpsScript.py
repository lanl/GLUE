import os
import numpy as np
import random
import csv
import zbar as z

def write_LammpsScript(Temperature,densities,charges,masses,system_index_species,box,cutoff,Teq,Trun,index_species,s_int,p_int,d_int):
    
    """
    This script takes thermodynamical conditions of a plasma: temperature, densities, ionisation state (zbars), masses, together with the number of
    "of elements in the system, simulation box and cutoff sizes [in units of Wigner-Seitz radius], equilibration and production number steps, to generate a LAMMPS script file.
    
    Author: Abdou Diaw
        """
    nspec=system_index_species

    with open('lammpsScript_'+str(nspec), 'w') as LammpsScript:
        
        
        # Once the zeros are removed estimte the number of species.
        #######################-----------------------------------------------#######################
        ## Estimate here parameters needed for the forces: screening length, force cutoff,
        ## time step, and drag frequency for thermostat.
        
        kb=       1.3807e-23
        hbar2=        1.1121811600000002e-68
        emass= 9.1094e-31
        eps0=8.8542e-12
        echarge= 1.6022e-19
        
        zbars=z.zBar(densities,charges, Temperature)
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

#        csv_writer = csv.writer(LammpsScript,delimiter=' ')
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
        csv_writer.writerow(['thermo',d_int])
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
        csv_writer.writerow(['#---------','Stress','tensors','---------#'])
        csv_writer.writerow('')
        S1=['variable','pxy', 'equal', 'pxy']
        S2=['variable','pxz', 'equal', 'pxz']
        S3=['variable','pyz', 'equal', 'pyz']
        V=l**3
        csv_writer.writerow('')
        csv_writer.writerow(['variable','scale_factor_v', 'equal', 1./(kb*Temp1)*V*s_int*dtstep])
        csv_writer.writerow(['variable','scale_factor_k', 'equal', s_int*dtstep/(kb*Temp1*Temp1)/V])
        csv_writer.writerow(S1)
        csv_writer.writerow(S2)
        csv_writer.writerow(S3)
        
        csv_writer.writerow('')
        csv_writer.writerow(['#---------','Heat', 'flux','tensors','---------#'])

        csv_writer.writerow('')
        
        csv_writer.writerow(['compute','myKE', 'all', 'ke/atom'])
        csv_writer.writerow(['compute','myPE', 'all', 'pe/atom'])
        csv_writer.writerow(['compute','myStress', 'all', 'stress/atom', 'NULL','virial'])
        csv_writer.writerow(['compute','flux', 'all', 'heat/flux', 'myKE','myPE', 'myStress'])
        csv_writer.writerow('')

        K1=['variable','Jx', 'equal', 'c_flux[1]/vol']
        K2=['variable','Jy', 'equal', 'c_flux[2]/vol']
        K3=['variable','Jz', 'equal', 'c_flux[3]/vol']
        
        csv_writer.writerow(K1)
        csv_writer.writerow(K2)
        csv_writer.writerow(K3)

        
        csv_writer.writerow('')
        csv_writer.writerow(['#---------','Compute','correlation', 'functions', 'and', 'integrals','over', 'time','---------#'])


        row_list=['thermo_style','custom', 'step','temp', 'press']

        csv_writer.writerow('')
 
        for s in range(len(densities)):
            csv_writer.writerow(['compute','vacf'+str(index_species[s]),'atom'+str(s+1),'vacf'])
            csv_writer.writerow(['fix',str(s+1),'atom'+str(s+1),'vector','1', 'c_vacf'+str(index_species[s])+'[4]'])
            csv_writer.writerow(['variable','Diff_'+str(s+1),'equal', '1.e4*dt*trap(f_'+str(s+1)+')'+'/3'])
            row_list.append('c_vacf'+str(index_species[s])+'[4]')
            csv_writer.writerow('')

        csv_writer.writerow(['#---------','viscosities', 'calculations','---------#'])
        csv_writer.writerow('')

        for s in range(len(densities)):
            csv_writer.writerow(['fix',str(s+1+len(densities)),'atom'+str(s+1),'ave/correlate',s_int,p_int,d_int,'&'])
            csv_writer.writerow(['v_pxy', 'v_pxz', 'v_pyz', 'type', 'auto', 'file', 'S0St'+str(s+1)+'.dat', 'ave', 'running'])
            csv_writer.writerow(['variable','v11_'+str(s+1),'equal', 'trap(f_'+str(s+1+len(densities))+'[3]'+')'+'*${scale_factor_v}'])
            csv_writer.writerow(['variable','v22_'+str(s+1),'equal', 'trap(f_'+str(s+1+len(densities))+'[4]'+')'+'*${scale_factor_v}'])
            csv_writer.writerow(['variable','v33_'+str(s+1),'equal', 'trap(f_'+str(s+1+len(densities))+'[5]'+')'+'*${scale_factor_v}'])
            row_list.append('v_v11_'+str(s+1))
            row_list.append('v_v22_'+str(s+1))
            row_list.append('v_v33_'+str(s+1))

            csv_writer.writerow('')

        csv_writer.writerow(['#---------','conductivities', 'calculations','---------#'])
        csv_writer.writerow('')
        
        for s in range(len(densities)):
            csv_writer.writerow(['fix',str(s+1+2*len(densities)),'atom'+str(s+1),'ave/correlate',s_int,p_int,d_int,'&'])
            csv_writer.writerow(['c_flux[3]', 'c_flux[4]', 'c_flux[5]', 'type', 'auto', 'file', 'profile.heatflux'+str(s+1)+'.dat', 'ave', 'running'])
            csv_writer.writerow(['variable','k11_'+str(s+1),'equal', 'trap(f_'+str(s+1+len(densities))+'[3]'+')'+'*${scale_factor_k}'])
            csv_writer.writerow(['variable','k22_'+str(s+1),'equal', 'trap(f_'+str(s+1+len(densities))+'[4]'+')'+'*${scale_factor_k}'])
            csv_writer.writerow(['variable','k33_'+str(s+1),'equal', 'trap(f_'+str(s+1+len(densities))+'[5]'+')'+'*${scale_factor_k}'])
            row_list.append('v_k11_'+str(s+1))
            row_list.append('v_k22_'+str(s+1))
            row_list.append('v_k33_'+str(s+1))
            csv_writer.writerow('')
        
        csv_writer.writerow('')

        csv_writer.writerow(row_list)
        csv_writer.writerow('')

        csv_writer.writerow(['#---------','Viscosity','coefficients', 'in', 'cm^2/s','---------#'])
        csv_writer.writerow('')
        
        for s in nspecies:
            for j in nspecies:
                if (s==j):
                    csv_writer.writerow(['variable','v'+str(index_species[s-1])+str(index_species[j-1]),'equal','(v_v11_'+str(s)+'+v_v22_'+str(s)+ '+v_v33_'+str(s)+')'+'/3.'])

        csv_writer.writerow('')
        csv_writer.writerow(['#---------','Conductivities','coefficients', 'in', 'cm^2/s','---------#'])
        csv_writer.writerow('')

        for s in nspecies:
            for j in nspecies:
                if (s==j):
                    csv_writer.writerow(['variable','k'+str(index_species[s-1])+str(index_species[j-1]),'equal','(v_k11_'+str(s)+'+v_k22_'+str(s)+ '+v_k33_'+str(s)+')'+'/3.'])


        csv_writer.writerow('')
        csv_writer.writerow(['#---------','Diffusion','coefficients', 'in', 'cm^2/s','---------#'])
        csv_writer.writerow('')

        for s in nspecies:
            for j in nspecies:
                if (s==j):
                    csv_writer.writerow(['variable','Diff_'+str(index_species[s-1])+str(index_species[j-1]),'equal', 'v_Diff_'+str(j)])

        csv_writer.writerow('')
        csv_writer.writerow('')

        csv_writer.writerow('')
        csv_writer.writerow(['run',Trun])

        csv_writer.writerow('')

# Print final values to files

        for s in nspecies:
            for j in nspecies:
                if (s==j):
                    csv_writer.writerow(['print','D=${Diff_'+str(index_species[s-1])+str(index_species[j-1])+'}','file','diffusion_coefficient_'+str(index_species[s-1])+str(index_species[j-1])+'.csv'])

        csv_writer.writerow('')
        for s in nspecies:
            for j in nspecies:
                if (s==j):
                    csv_writer.writerow(['print','v=${v'+str(index_species[s-1])+str(index_species[j-1])+'}','file','viscosity_coefficient_'+str(index_species[s-1])+str(index_species[j-1])+'.csv'])
        csv_writer.writerow('')

        for s in nspecies:
            for j in nspecies:
                if (s==j):
                    csv_writer.writerow(['print','k=${k'+str(index_species[s-1])+str(index_species[j-1])+'}','file','conductivity_coefficient_'+str(index_species[s-1])+str(index_species[j-1])+'.csv'])
        csv_writer.writerow('')
    return LammpsScript

