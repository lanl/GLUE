import numpy as np
import os
import random
import csv

e2 = 1.44e-7
pi = np.pi

"""
This module computes single species and binary transport coefficients based on the paper of 
 L. G. Stanton and M. S. Murillo "Ionic transport in high-energy-density
matter", PRE ${\bf 93}$ 043203 (2016).  
"""
class sm:
    @staticmethod
    def D(n,m,Z,T):
        """Computes self-diffusion coefficient of a single species.
            Input:  n     - 1/cm^3
            m     - g
            Z     - unitless
            T     - eV
            
            Output: eta   - cm^2/ s
            """
        
        
        erg_to_ev = 6.2415e11
        
        # charge squared (eV - cm)
        e2 = 1.44e-7
        
        #ion radius calculation
        a = (3.0/(4.0*np.pi*n))**(1.0/3.0)
        
        Gamma = Z*Z*e2/a/T     #unitless
        
        lam = lam_eff1(n,m,Z,T)
        k = a / lam        #unitless
        gamma = Gamma*np.sqrt( k**2 + (4.0*pi*Z*Z*e2*n*a*a)/(T*(1.0 + 3.0*Gamma)))


        D = 3.0*T**2.5 / (16*np.sqrt(pi*m)*n*Z**4.0*e2*e2*K11(gamma)) / np.sqrt(erg_to_ev)
        wp = np.sqrt(4.0*pi*Z**2 * n * e2 / m / erg_to_ev)
        D_star = D/a**2/wp
        return D,D_star

    @staticmethod
    def Lmf(n,m,Z,T):
        vth=1.e2*np.sqrt(8*1.38e-23*T*11600/(np.pi*m*1.e-3))

        return 3*D(n,m,Z,T)/vth


    @staticmethod
    def mfp(n,m,Z,T):
        vth=np.sqrt(8*1.38e-23*T*11600/(np.pi*m*1.e-3))
        mpf=3*D(n,m,Z,T)*1.e-4/vth
        return 3*sm.D(n,m,Z,T)*1.e-4/vth

    @staticmethod
    def eta(n,m,Z,T,kappa=-1):
        """Computes viscosity coefficient of a single species. 
        Input:  n     - 1/cm^3
                m     - g
                Z     - unitless
                T     - eV

        Output: eta   - g / (cm s)
        """


        erg_to_ev = 6.2415e11
        
    # charge squared (eV - cm)
        e2 = 1.44e-7
                                    
    #ion radius calculation
        a = (3.0/(4.0*np.pi*n))**(1.0/3.0)
        
        Gamma = Z*Z*e2/a/T     #unitless

        if kappa == -1:
            lam = lam_eff1(n,m,Z,T)
            k = a / lam        #unitless
            gamma = Gamma*np.sqrt( k**2 + (4.0*pi*Z*Z*e2*n*a*a)/(T*(1.0 + 3.0*Gamma)))
        else:
            gamma = Gamma*np.sqrt( kappa**2 + (4.0*pi*Z*Z*e2*n*a*a)/(T*(1.0 + 3.0*Gamma)))

        
        eta = 5.0*np.sqrt(m)*T**2.5 / (16*np.sqrt(pi)*Z**4.0 * e2*e2*K22(gamma)) / np.sqrt(erg_to_ev)        

        wp = np.sqrt(4.0*pi*Z**2 * n * e2 / (0.5*(m + m)) / erg_to_ev)
        
        eta_star = eta / m / n / wp / a / a

    #    return eta, eta_star
        return  eta_star

    @staticmethod
    def Ktherm1(n,m,Z,T,kappa=-1):
        """Computes thermal conductivity coefficient of a single species. 
        Input:  n     - 1/cm^3
                m     - g
                Z     - unitless
                T     - eV

        Output: K     - 1 / (cm s)
        """

        erg_to_ev = 6.2415e11
        
    # charge squared (eV - cm)
        e2 = 1.44e-7
                        
    #ion radius calculation
        a = (3.0/(4.0*np.pi*n))**(1.0/3.0)

        Gamma = Z*Z*e2/a/T     #unitless

        if kappa == -1:
            lam = lam_eff1(n,m,Z,T)
            k = a / lam        #unitless
            gamma = Gamma*np.sqrt( k**2 + (4.0*pi*Z*Z*e2*n*a*a)/(T*(1.0 + 3.0*Gamma)))
        else:
            gamma = Gamma*np.sqrt( kappa**2 + (4.0*pi*Z*Z*e2*n*a*a)/(T*(1.0 + 3.0*Gamma)))
        
        Ktherm = 75.0*T**2.5 / (64.0*np.sqrt(pi*m)*Z**4.0 * e2*e2 * K22(gamma)) / np.sqrt(erg_to_ev) 

        wp = np.sqrt(4.0*pi*Z**2 * n * e2 / (0.5*(m + m)) / erg_to_ev)
        
        K_star = Ktherm / n / wp / a / a
            
        return Ktherm, K_star

    @staticmethod
    def D_ij(n1,n2,m1,m2,Z1,Z2,T,kappa=-1):
        """Calculates diffusion coefficient D_ij for a binary mixture based on the 
        Stanton-Murillo transport coefficient formulas. 

        Q : what does this assume for kappa???

        Input: n1         - 1/cm^3
                n2         - 1/cm^3
                m1         - g
                m2         - g
                Z1         
                Z2      
                T          - eV

        Output D_ij       - cm^2 / s
        """
        
    # charge squared (eV - cm)
        e2_cgs = 1.44e-7              
        erg_to_ev = 6.2415e11

        mu = m1*m2/(m1 + m2)
        n = n1 + n2
        
    #ion radius calculation
        atot = (3.0/(4.0*np.pi*n))**(1.0/3.0)

        g_12 = gammaSM2(n1,n2,m1,m2,Z1,Z2,T,atot,kappa)

        Omega12_11 = np.sqrt(2.0*np.pi/mu/erg_to_ev) * (Z1*Z2*e2_cgs)**2.0 / T**1.5 * K11(g_12)

        D_ij = 3.0*T / (16.0*n*mu*Omega12_11) / erg_to_ev 
    
        wp = np.sqrt(4.0*pi*(0.5*(Z1 + Z2))**2 * n * e2 / (0.5*(m1 + m2)) / erg_to_ev)
        
        D_ij_star = D_ij / atot**2 / wp

        return D_ij

    @staticmethod
    def eta2(n1,n2,m1,m2,Z1,Z2,T):
        """Calculates viscosity coefficient eta_tot for a binary mixture based on the 
        Stanton-Murillo transport coefficient formulas. 

        Input: n1         - 1/cm^3
                n2         - 1/cm^3
                m1         - g
                m2         - g
                Z1         
                Z2      
                T          - eV

        Output eta_ij     - g / (cm s)
        """

        e2_cgs = 1.44e-7       #ev-cm
        erg_to_ev = 6.2415e11


        mu = m1*m2/(m1 + m2)   #g
        M1 = m1/(m1 + m2)
        M2 = m2/(m1 + m2)


        n = n1 + n2            #1/cm^3
        n_e = Z1*n1 + Z2*n2

        x1 = n1/n
        x2 = n2/n
        
        
        lam = lam_eff2(n1,n2,m1,m2,Z1,Z2,T)

        #CE Variables defined in MS - initialized here to keep track of those I need to do!

        A = 0
        E = 0

        eta_1 = 0
        eta_2 = 0

        R1 = 0
        R2 = 0
        R12 = 0
        R12p = 0
        
        Omega11_11 = 0
        Omega11_22 = 0
        Omega22_11 = 0
        Omega22_22 = 0
        Omega12_11 = 0
        Omega12_22 = 0

        #The actual calculations
        #Omega units: cm^3/s

        g_11 = Z1*Z1*e2_cgs/lam/T
        Omega11_11 = np.sqrt(2.0*np.pi/m1/erg_to_ev) * (Z1*Z1*e2_cgs)**2.0 / T**1.5 * K11(g_11) 
        Omega11_22 = np.sqrt(2.0*np.pi/m1/erg_to_ev) * (Z1*Z1*e2_cgs)**2.0 / T**1.5 * K22(g_11)

        g_22 = Z2*Z2*e2_cgs/lam/T
        Omega22_11 = np.sqrt(2.0*np.pi/m2/erg_to_ev) * (Z2*Z2*e2_cgs)**2.0 / T**1.5 * K11(g_22)
        Omega22_22 = np.sqrt(2.0*np.pi/m2/erg_to_ev) * (Z2*Z2*e2_cgs)**2.0 / T**1.5 * K22(g_22)

        g_12 = Z1*Z2*e2_cgs/lam/T
        Omega12_11 = np.sqrt(2.0*np.pi/mu/erg_to_ev) * (Z1*Z2*e2_cgs)**2.0 / T**1.5 * K11(g_12)
        Omega12_22 = np.sqrt(2.0*np.pi/mu/erg_to_ev) * (Z1*Z2*e2_cgs)**2.0 / T**1.5 * K22(g_12)
        
        eta_1 = 5.0*T/Omega11_22/8.0/erg_to_ev       #g/(cm s)
        eta_2 = 5.0*T/Omega22_22/8.0/erg_to_ev       #g/(cm s)

        A = Omega12_22/Omega12_11/5.0               #unitless

        E = T / (8.0*M1*M2*Omega12_11)/erg_to_ev    #g/(cm s)
        
        R1 = 2.0/3.0 + M1/M2 * A                    #unitless
        R2 = 2.0/3.0 + M2/M1 * A                    #unitless
        
        R12  = 4.0*A/(3.0*M1*M2*E) + E/(2.0*eta_1*eta_2)  #cm s / g
        R12p = 4.0/3.0 + 0.5*E/eta_1 + 0.5*E/eta_2 - 2.0*A #unitless

        etatot = (x1*x1*R1 + x2*x2*R2 + x1*x2*R12p)/(x1*x1*R1/eta_1 + x2*x2*R2/eta_2 + x1*x2*R12)

        return etatot  #units g / cm s

    @staticmethod
    def Ktherm2(n1,n2,m1,m2,Z1,Z2,T):
        """Calculates Thermal conductivity coefficient K_tot for a binary mixture based on the 
        Stanton-Murillo transport coefficient formulas. 

        Input: n1         - 1/cm^3
                n2         - 1/cm^3
                m1         - g
                m2         - g
                Z1         
                Z2      
                T          - eV

        Output K_ij       - 1 / (cm s)
        """

        e2_cgs = 1.44e-7       #ev-cm
        erg_to_ev = 6.2415e11
        m_e = 9.109e-28        #g
        hbar = 6.5821e-16      #eV-s
        pi = np.pi
        

        mu = m1*m2/(m1 + m2)   #g
        M1 = m1/(m1 + m2)
        M2 = m2/(m1 + m2)


        n = n1 + n2            #1/cm^3
        n_e = Z1*n1 + Z2*n2

        x1 = n1/n
        x2 = n2/n

        lam = lam_eff2(n1,n2,m1,m2,Z1,Z2,T)

        #CE Variables defined in MS - initialized here to keep track of those I need to do!

        A = 0
        E = 0

        K1 = 0
        K2 = 0

        R1 = 0
        R2 = 0
        R12 = 0
        R12p = 0
        
        Omega11_22 = 0
        Omega22_22 = 0
        Omega12_11 = 0
        Omega12_22 = 0
        Omega12_12 = 0
        Omega12_13 = 0

        #The actual calculations
        #Omega units: cm^3/s

        g_11 = Z1*Z1*e2_cgs/lam/T
        Omega11_22 = np.sqrt(2.0*np.pi/mu/erg_to_ev) * (Z1*Z1*e2_cgs)**2.0 / T**1.5 * K22(g_11)

        g_22 = Z2*Z2*e2_cgs/lam/T
        Omega22_22 = np.sqrt(2.0*np.pi/mu/erg_to_ev) * (Z2*Z2*e2_cgs)**2.0 / T**1.5 * K22(g_22)

        g_12 = Z1*Z2*e2_cgs/lam/T
        Omega12_11 = np.sqrt(2.0*np.pi/mu/erg_to_ev) * (Z1*Z2*e2_cgs)**2.0 / T**1.5 * K11(g_12)
        Omega12_22 = np.sqrt(2.0*np.pi/mu/erg_to_ev) * (Z1*Z2*e2_cgs)**2.0 / T**1.5 * K22(g_12)
        Omega12_12 = np.sqrt(2.0*np.pi/mu/erg_to_ev) * (Z1*Z2*e2_cgs)**2.0 / T**1.5 * K12(g_12)
        Omega12_13 = np.sqrt(2.0*np.pi/mu/erg_to_ev) * (Z1*Z2*e2_cgs)**2.0 / T**1.5 * K13(g_12)
        
        #eta1 = 5.0*T/8.0/Omega11_22 / erg_to_ev   #g / cm s
        #eta2 = 5.0*T/8.0/Omega22_22 / erg_to_ev   #g / cm s

        K1 = 75.0*T/(32.0*m1*Omega11_22) / erg_to_ev  #1 / cm s
        K2 = 75.0*T/(32.0*m2*Omega22_22) / erg_to_ev  #1 / cm s

        A = Omega12_22/Omega12_11/5.0               #unitless

        B = (5.0*Omega12_12 - Omega12_13)/5.0/Omega12_11 #unitless

        E = T / (8.0*M1*M2*Omega12_11)/erg_to_ev    #g/(cm s)
        
        P1 = Omega11_22 / (5.0*M2*Omega12_11)    #unitless
        P2 = Omega22_22 / (5.0*M1*Omega12_11)    #unitless
        
        Q1 = P1*(6.0*M2*M2 + 5.0*M1*M1 - 4.0*M1*M1*B + 8.0*M1*M2*A) #unitless
        Q2 = P2*(6.0*M1*M1 + 5.0*M2*M2 - 4.0*M2*M2*B + 8.0*M1*M2*A) #unitless

        Q12 = 2.0*P1*P2 + 3.0*(M1 - M2)**2 * (5.0 - 4.0*B) + 4.0 * M1*M2*A*(11.0 - 4.0*B) #unitless
        Q12p = 15.0*E*(P1 + P2 + (11.0 - 4.0*B - 8.0*A)*M1*M2)/(2.0*(m1 + m2)) #1 / cm s

        K = (x1*x1*Q1*K1 + x2*x2*Q2*K2 + x1*x2*Q12p)/(x1*x1*Q1 + x2*x2*Q2 + x1*x2*Q12) #1 / cm s

        return K #units 1 / (cm s)

    @staticmethod
    def K11(g):
        if g < 1.0:
            return -0.25*np.log(1.466*g - 1.7836*g**2.0 + 1.4313*g**3.0 - 0.55833*g**4 + 0.061162*g**5)
        else:
            return (0.081033 - 0.091336*np.log(g) + 0.05176*np.log(g)**2)/(1.0 - 0.50026*g + 0.17044*g*g)

    @staticmethod
    def K12(g):
        if g < 1.0:
            return -0.25*np.log(0.52094*g + 0.25153*g**2.0 - 1.1337*g**3.0 + 1.2155*g**4 - 0.43784*g**5)
        else:
            return (0.20572 - 0.16536*np.log(g) + 0.061572*np.log(g)**2)/(1.0 - 0.12770*g + 0.066993*g*g)

    @staticmethod
    def K13(g):
        if g < 1.0:
            return -0.5*np.log(0.30346*g + 0.23739*g**2.0 - 0.62167*g**3.0 + 0.56110*g**4 - 0.18046*g**5)
        else:
            return (0.68375 - 0.384596*np.log(g) + 0.10711*np.log(g)**2)/(1.0 + 0.10649*g + 0.028760*g*g)

    @staticmethod
    def K22(g):
        if g < 1.0:
            return -0.5*np.log(0.8541*g - 0.22898*g**2.0 - 0.60059*g**3.0 + 0.80591*g**4 - 0.30555*g**5)
        else:
            return (0.43475 - 0.21147*np.log(g) + 0.11116*np.log(g)**2)/(1.0 + 0.19665*g + 0.15195*g*g)

    @staticmethod
    def lam_eff1(n,m,Z,T):
        #note - this assumes ion and electron temperatures are the same

        m_e = 9.109e-28        #g
        hbar = 6.5821e-16      #eV-s
        pi = np.pi
        erg_to_ev = 6.2415e11  
        e2_cgs = 1.44e-7       #eV-cm

        n_e = Z*n              #1/cc 

        #define screening length

        EF = hbar*hbar*(3.0*pi*pi*n_e)**(2.0/3.0) / (2.0*m_e) / erg_to_ev   #eV
        lam_e = 4*pi*e2_cgs*n_e/np.sqrt(T*T + 4.0*EF*EF/9.0)                  #1/cm^2, this is really 1/lam_e

        a = (3.0*Z /(4.0*pi*n_e) )**(1.0/3.0)
        lam_1 = 4.0*pi*e2_cgs*n/T                                          #1/cm^2, this is reall 1/lam_1
        Gam1 = Z*Z*e2_cgs/a/T

        lam = lam_e + lam_1/(1.0 + 3.0*Gam1)
        lam = 1.0/np.sqrt(lam)

        return lam

    @staticmethod
    def lam_e(n1,n2,m1,m2,Z1,Z2,T):

        #note - this assumes ion and electron temperatures are the same

        m_e = 9.109e-28        #g
        hbar = 6.5821e-16      #eV-s
        pi = np.pi
        erg_to_ev = 6.2415e11
        e2_cgs = 1.44e-7       #eV-cm
        
        mu = m1*m2/(m1 + m2)   #g
        M1 = m1/(m1 + m2)
        M2 = m2/(m1 + m2)


        n = n1 + n2            #1/cm^3
        n_e = Z1*n1 + Z2*n2

        x1 = n1/n
        x2 = n2/n

        #define screening length

        EF = hbar*hbar*(3.0*pi*pi*n_e)**(2.0/3.0) / (2.0*m_e) / erg_to_ev   #eV
        lam = 4*pi*e2_cgs*n_e/np.sqrt(T*T + 4.0*EF*EF/9.0)                  #1/cm^2, this is really 1/lam_e


        return lam

    @staticmethod
    def lam_eff2(n1,n2,m1,m2,Z1,Z2,T):

        #note - this assumes ion and electron temperatures are the same

        m_e = 9.109e-28        #g
        hbar = 6.5821e-16      #eV-s
        pi = np.pi
        erg_to_ev = 6.2415e11
        e2_cgs = 1.44e-7       #eV-cm
        
        mu = m1*m2/(m1 + m2)   #g
        M1 = m1/(m1 + m2)
        M2 = m2/(m1 + m2)


        n = n1 + n2            #1/cm^3
        n_e = Z1*n1 + Z2*n2

        x1 = n1/n
        x2 = n2/n

        #define screening length

        EF = hbar*hbar*(3.0*pi*pi*n_e)**(2.0/3.0) / (2.0*m_e) / erg_to_ev   #eV
        lam_e = 4*pi*e2_cgs*n_e/np.sqrt(T*T + 4.0*EF*EF/9.0)                  #1/cm^2, this is really 1/lam_e

        a_1 = (3.0*Z1 /(4.0*pi*n_e) )**(1.0/3.0)
        lam_1 = 4.0*pi*Z1*Z1*e2_cgs*n1/T                                          #1/cm^2, this is reall 1/lam_1
        Gam1 = Z1*Z1*e2_cgs/a_1/T

        a_2 = (3.0*Z2 /(4.0*pi*n_e) )**(1.0/3.0)
        lam_2 = 4.0*pi*Z2*Z2*e2_cgs*n2/T                                          #1/cm^2
        Gam2 = Z2*Z2*e2_cgs/a_2/T


        lam = lam_e + lam_1/(1.0 + 3.0*Gam1) + lam_2/(1.0 + 3.0*Gam2)
        lam = 1.0/np.sqrt(lam)

        return lam

    @staticmethod
    def gammaSM2(n1,n2,m1,m2,Z1,Z2,T,atot,kappa):
        """Computes the K_ij coefficient gamma for a binary mixture"""

        n = n1 + n2
        rhotot = Z1*n1 + Z2*n2

        if kappa == -1:

            lam = lam_eff2(n1,n2,m1,m2,Z1,Z2,T)
            
            gamma = Z1*Z2*e2/lam/T
        else:
            x1 = n1/n
            z1 = Z1*n1/rhotot
            x2 = n2/n
            z2 = Z2*n2/rhotot
            Gamma = Z1*Z2*e2/atot/T
            Gamma11 = Z1*Z1*e2/atot/T
            Gamma22 = Z2*Z2*e2/atot/T
            gamma = Gamma*np.sqrt( kappa**2 + 3.0*x1*Gamma11/(1.0 + 3.0*Gamma11*(x1/z1)**(1.0/3.0)) 
                                + 3.0*x2*Gamma22/(1.0 + 3.0*Gamma22*(x2/z2)**(1.0/3.0)) )
        return gamma

    @staticmethod
    def mfp(n1,m1,Z1,T,kappa=-1):
        
        D=D_ij(n1,n1,m1,m1,Z1,Z1,T,kappa=-1)
        mred = m1*m1/(m1+m1)
        #    vth=2.02e-06*np.sqrt(T/(np.pi*mred))
        vth=np.sqrt(8*1.38e-23*T*11600/(np.pi*mred*1.e-3))
        return 3*D*1.e-4/vth

    @staticmethod
    def Wigner_Seitz_radius(n):
        return (3./(4.*np.pi*n))**(1./3.)


def D(n,m,Z,T):
    """Computes self-diffusion coefficient of a single species.
        Input:  n     - 1/cm^3
        m     - g
        Z     - unitless
        T     - eV
        
        Output: eta   - cm^2/ s
        """
    
    
    erg_to_ev = 6.2415e11
    
    # charge squared (eV - cm)
    e2 = 1.44e-7
    
    #ion radius calculation
    a = (3.0/(4.0*np.pi*n))**(1.0/3.0)
    
    Gamma = Z*Z*e2/a/T     #unitless
    
    lam = lam_eff1(n,m,Z,T)
    k = a / lam        #unitless
    gamma = Gamma*np.sqrt( k**2 + (4.0*pi*Z*Z*e2*n*a*a)/(T*(1.0 + 3.0*Gamma)))
    
    
    D = 3.0*T**2.5 / (16*np.sqrt(pi*m)*n*Z**4.0*e2*e2*K11(gamma)) / np.sqrt(erg_to_ev)
    
    return D

def Lmf(n,m,Z,T):
    vth=1.e2*np.sqrt(8*1.38e-23*T*11600/(np.pi*m*1.e-3))
    
    return 3*D(n,m,Z,T)/vth

def mfp(n,m,Z,T):
    vth=np.sqrt(8*1.38e-23*T*11600/(np.pi*m*1.e-3))
    mpf=3*D(n,m,Z,T)*1.e-4/vth
    return 3*sm.D(n,m,Z,T)*1.e-4/vth

def eta(n,m,Z,T,kappa=-1):
    """Computes viscosity coefficient of a single species.
        Input:  n     - 1/cm^3
        m     - g
        Z     - unitless
        T     - eV
        
        Output: eta   - Pa.s
        """
    
    
    erg_to_ev = 6.2415e11
    
    # charge squared (eV - cm)
    e2 = 1.44e-7
    
    #ion radius calculation
    a = (3.0/(4.0*np.pi*n))**(1.0/3.0)
    
    Gamma = Z*Z*e2/a/T     #unitless
    
    if kappa == -1:
        lam = lam_eff1(n,m,Z,T)
        k = a / lam        #unitless
        gamma = Gamma*np.sqrt( k**2 + (4.0*pi*Z*Z*e2*n*a*a)/(T*(1.0 + 3.0*Gamma)))
    else:
        gamma = Gamma*np.sqrt( kappa**2 + (4.0*pi*Z*Z*e2*n*a*a)/(T*(1.0 + 3.0*Gamma)))
    
    
    eta = 5.0*np.sqrt(m)*T**2.5 / (16*np.sqrt(pi)*Z**4.0 * e2*e2*K22(gamma)) / np.sqrt(erg_to_ev)
    return  0.1*eta

def Ktherm1(n,m,Z,T,kappa=-1):
    """Computes thermal conductivity coefficient of a single species.
        Input:  n     - 1/cm^3
        m     - g
        Z     - unitless
        T     - eV
        
        Output: K     - W/m/K
        """
    
    erg_to_ev = 6.2415e11
    
    # charge squared (eV - cm)
    e2 = 1.44e-7
    
    #ion radius calculation
    a = (3.0/(4.0*np.pi*n))**(1.0/3.0)
    
    Gamma = Z*Z*e2/a/T     #unitless
    
    if kappa == -1:
        lam = lam_eff1(n,m,Z,T)
        k = a / lam        #unitless
        gamma = Gamma*np.sqrt( k**2 + (4.0*pi*Z*Z*e2*n*a*a)/(T*(1.0 + 3.0*Gamma)))
    else:
        gamma = Gamma*np.sqrt( kappa**2 + (4.0*pi*Z*Z*e2*n*a*a)/(T*(1.0 + 3.0*Gamma)))
    
    Ktherm = 75.0*T**2.5 / (64.0*np.sqrt(pi*m)*Z**4.0 * e2*e2 * K22(gamma)) / np.sqrt(erg_to_ev)
    
    
    return 1.e2*1.38e-23*Ktherm


def D_ij(n1,n2,m1,m2,Z1,Z2,T,kappa=-1):
    """Calculates diffusion coefficient D_ij for a binary mixture based on the
        Stanton-Murillo transport coefficient formulas.
        
        Q : what does this assume for kappa???
        
        Input: n1         - 1/cm^3
        n2         - 1/cm^3
        m1         - g
        m2         - g
        Z1
        Z2
        T          - eV
        
        Output D_ij       - cm^2 / s
        """
    
    # charge squared (eV - cm)
    e2_cgs = 1.44e-7
    erg_to_ev = 6.2415e11
    
    mu = m1*m2/(m1 + m2)
    n = n1 + n2
    
    #ion radius calculation
    atot = (3.0/(4.0*np.pi*n))**(1.0/3.0)
    
    g_12 = gammaSM2(n1,n2,m1,m2,Z1,Z2,T,atot,kappa)
    
    Omega12_11 = np.sqrt(2.0*np.pi/mu/erg_to_ev) * (Z1*Z2*e2_cgs)**2.0 / T**1.5 * K11(g_12)
    
    D_ij = 3.0*T / (16.0*n*mu*Omega12_11) / erg_to_ev
    
    
    return D_ij

def eta2(n1,n2,m1,m2,Z1,Z2,T):
    """Calculates viscosity coefficient eta_tot for a binary mixture based on the
        Stanton-Murillo transport coefficient formulas.
        
        Input: n1         - 1/cm^3
        n2         - 1/cm^3
        m1         - g
        m2         - g
        Z1
        Z2
        T          - eV
        
        Output eta_ij     - Pa.s
        """
    
    e2_cgs = 1.44e-7       #ev-cm
    erg_to_ev = 6.2415e11
    
    
    mu = m1*m2/(m1 + m2)   #g
    M1 = m1/(m1 + m2)
    M2 = m2/(m1 + m2)
    
    
    n = n1 + n2            #1/cm^3
    n_e = Z1*n1 + Z2*n2
    
    x1 = n1/n
    x2 = n2/n
    
    
    lam = lam_eff2(n1,n2,m1,m2,Z1,Z2,T)
    
    #CE Variables defined in MS - initialized here to keep track of those I need to do!
    
    A = 0
    E = 0
    
    eta_1 = 0
    eta_2 = 0
    
    R1 = 0
    R2 = 0
    R12 = 0
    R12p = 0
    
    Omega11_11 = 0
    Omega11_22 = 0
    Omega22_11 = 0
    Omega22_22 = 0
    Omega12_11 = 0
    Omega12_22 = 0
    
    #The actual calculations
    #Omega units: cm^3/s
    
    g_11 = Z1*Z1*e2_cgs/lam/T
    Omega11_11 = np.sqrt(2.0*2.0*np.pi/m1/erg_to_ev) * (Z1*Z1*e2_cgs)**2.0 / T**1.5 * K11(g_11)
    Omega11_22 = np.sqrt(2.0*2.0*np.pi/m1/erg_to_ev) * (Z1*Z1*e2_cgs)**2.0 / T**1.5 * K22(g_11)
    
    g_22 = Z2*Z2*e2_cgs/lam/T
    Omega22_11 = np.sqrt(2.0*2.0*np.pi/m2/erg_to_ev) * (Z2*Z2*e2_cgs)**2.0 / T**1.5 * K11(g_22)
    Omega22_22 = np.sqrt(2.0*2.0*np.pi/m2/erg_to_ev) * (Z2*Z2*e2_cgs)**2.0 / T**1.5 * K22(g_22)
    
    g_12 = Z1*Z2*e2_cgs/lam/T
    Omega12_11 = np.sqrt(2.0*np.pi/mu/erg_to_ev) * (Z1*Z2*e2_cgs)**2.0 / T**1.5 * K11(g_12)
    Omega12_22 = np.sqrt(2.0*np.pi/mu/erg_to_ev) * (Z1*Z2*e2_cgs)**2.0 / T**1.5 * K22(g_12)
    
    eta_1 = 5.0*T/Omega11_22/8.0/erg_to_ev       #g/(cm s)
    eta_2 = 5.0*T/Omega22_22/8.0/erg_to_ev       #g/(cm s)
    
    A = Omega12_22/Omega12_11/5.0               #unitless
    
    E = T / (8.0*M1*M2*Omega12_11)/erg_to_ev    #g/(cm s)
    
    R1 = 2.0/3.0 + M1/M2 * A                    #unitless
    R2 = 2.0/3.0 + M2/M1 * A                    #unitless
    
    R12  = 4.0*A/(3.0*M1*M2*E) + E/(2.0*eta_1*eta_2)  #cm s / g
    R12p = 4.0/3.0 + 0.5*E/eta_1 + 0.5*E/eta_2 - 2.0*A #unitless
    
    etatot = (x1*x1*R1 + x2*x2*R2 + x1*x2*R12p)/(x1*x1*R1/eta_1 + x2*x2*R2/eta_2 + x1*x2*R12)
    
    return 0.1*etatot  #units Pa.s

def Ktherm2(n1,n2,m1,m2,Z1,Z2,T):
    """Calculates Thermal conductivity coefficient K_tot for a binary mixture based on the
        Stanton-Murillo transport coefficient formulas.
        
        Input: n1         - 1/cm^3
        n2         - 1/cm^3
        m1         - g
        m2         - g
        Z1
        Z2
        T          - eV
        
        Output K_ij       - W/m/K
        """
    
    e2_cgs = 1.44e-7       #ev-cm
    erg_to_ev = 6.2415e11
    m_e = 9.109e-28        #g
    hbar = 6.5821e-16      #eV-s
    pi = np.pi
    
    
    mu = m1*m2/(m1 + m2)   #g
    M1 = m1/(m1 + m2)
    M2 = m2/(m1 + m2)
    
    
    n = n1 + n2            #1/cm^3
    n_e = Z1*n1 + Z2*n2
    
    x1 = n1/n
    x2 = n2/n
    
    lam = lam_eff2(n1,n2,m1,m2,Z1,Z2,T)
    
    #CE Variables defined in MS - initialized here to keep track of those I need to do!
    
    A = 0
    E = 0
    
    K1 = 0
    K2 = 0
    
    R1 = 0
    R2 = 0
    R12 = 0
    R12p = 0
    
    Omega11_22 = 0
    Omega22_22 = 0
    Omega12_11 = 0
    Omega12_22 = 0
    Omega12_12 = 0
    Omega12_13 = 0
    
    #The actual calculations
    #Omega units: cm^3/s
    
    g_11 = Z1*Z1*e2_cgs/lam/T
    Omega11_22 = np.sqrt(2.0*2.0*np.pi/m1/erg_to_ev) * (Z1*Z1*e2_cgs)**2.0 / T**1.5 * K22(g_11)
    
    g_22 = Z2*Z2*e2_cgs/lam/T
    Omega22_22 = np.sqrt(2.0*2.0*np.pi/m2/erg_to_ev) * (Z2*Z2*e2_cgs)**2.0 / T**1.5 * K22(g_22)
    
    g_12 = Z1*Z2*e2_cgs/lam/T
    Omega12_11 = np.sqrt(2.0*np.pi/mu/erg_to_ev) * (Z1*Z2*e2_cgs)**2.0 / T**1.5 * K11(g_12)
    Omega12_22 = np.sqrt(2.0*np.pi/mu/erg_to_ev) * (Z1*Z2*e2_cgs)**2.0 / T**1.5 * K22(g_12)
    Omega12_12 = np.sqrt(2.0*np.pi/mu/erg_to_ev) * (Z1*Z2*e2_cgs)**2.0 / T**1.5 * K12(g_12)
    Omega12_13 = np.sqrt(2.0*np.pi/mu/erg_to_ev) * (Z1*Z2*e2_cgs)**2.0 / T**1.5 * K13(g_12)
    
    
    K1 = 75.0*T/(32.0*m1*Omega11_22) / erg_to_ev  #1 / cm s
    K2 = 75.0*T/(32.0*m2*Omega22_22) / erg_to_ev  #1 / cm s
    
    A = Omega12_22/Omega12_11/5.0               #unitless
    
    B = (5.0*Omega12_12 - Omega12_13)/5.0/Omega12_11 #unitless
    
    E = T / (8.0*M1*M2*Omega12_11)/erg_to_ev    #g/(cm s)
    
    P1 = Omega11_22 / (5.0*M2*Omega12_11)    #unitless
    P2 = Omega22_22 / (5.0*M1*Omega12_11)    #unitless
    
    Q1 = P1*(6.0*M2*M2 + 5.0*M1*M1 - 4.0*M1*M1*B + 8.0*M1*M2*A) #unitless
    Q2 = P2*(6.0*M1*M1 + 5.0*M2*M2 - 4.0*M2*M2*B + 8.0*M1*M2*A) #unitless
    
    Q12 = 2.0*P1*P2 + 3.0*(M1 - M2)**2 * (5.0 - 4.0*B) + 4.0 * M1*M2*A*(11.0 - 4.0*B) #unitless
    Q12p = 15.0*E*(P1 + P2 + (11.0 - 4.0*B - 8.0*A)*M1*M2)/(2.0*(m1 + m2)) #1 / cm s
    
    K = (x1*x1*Q1*K1 + x2*x2*Q2*K2 + x1*x2*Q12p)/(x1*x1*Q1 + x2*x2*Q2 + x1*x2*Q12) #1 / cm s
    
    
    
    return 1.e2*1.38e-23*K #units W/m/K

def K22(g):
    k22_WC=-0.5*np.log(0.85401*g-0.22898*g**2-0.60059*g**3+ 0.80591*g**4-0.30555*g**5)
    k22_SC=(0.43475-0.21147*np.log(g)+0.11116*(np.log(g))**2)/(1.+0.19665*g+0.15195*g**2)
    
    return np.where(g < 1., k22_WC, k22_SC)

def K11(g):
    
    k11_WC = -0.25*np.log(1.466*g - 1.7836*g**2.0 + 1.4313*g**3.0 - 0.55833*g**4 + 0.061162*g**5)
    k11_SC = (0.081033 - 0.091336*np.log(g) + 0.05176*np.log(g)**2)/(1.0 - 0.50026*g + 0.17044*g*g)
    
    return np.where(g < 1., k11_WC, k11_SC)

def K12(g):
    k12_WC=-0.25*np.log(0.52094*g + 0.25153*g**2.0 - 1.1337*g**3.0 + 1.2155*g**4 - 0.43784*g**5)
    k12_SC = (0.20572 - 0.16536*np.log(g) + 0.061572*np.log(g)**2)/(1.0 - 0.12770*g + 0.066993*g*g)
    return np.where(g < 1., k12_WC, k12_SC)

def K13(g):
    
    k13_WC= -0.5*np.log(0.30346*g + 0.23739*g**2.0 - 0.62167*g**3.0 + 0.56110*g**4 - 0.18046*g**5)
    k13_SC=(0.68375 - 0.384596*np.log(g) + 0.10711*np.log(g)**2)/(1.0 + 0.10649*g + 0.028760*g*g)
    return np.where(g < 1., k13_WC, k13_SC)

def lam_eff1(n,m,Z,T):
    #note - this assumes ion and electron temperatures are the same
    
    m_e = 9.109e-28        #g
    hbar = 6.5821e-16      #eV-s
    pi = np.pi
    erg_to_ev = 6.2415e11
    e2_cgs = 1.44e-7       #eV-cm
    
    n_e = Z*n              #1/cc
    
    #define screening length
    
    EF = hbar*hbar*(3.0*pi*pi*n_e)**(2.0/3.0) / (2.0*m_e) / erg_to_ev   #eV
    lam_e = 4*pi*e2_cgs*n_e/np.sqrt(T*T + 4.0*EF*EF/9.0)                  #1/cm^2, this is really 1/lam_e
    
    a = (3.0*Z /(4.0*pi*n_e) )**(1.0/3.0)
    lam_1 = 4.0*pi*e2_cgs*n/T                                          #1/cm^2, this is reall 1/lam_1
    Gam1 = Z*Z*e2_cgs/a/T
    
    lam = lam_e + lam_1/(1.0 + 3.0*Gam1)
    lam = 1.0/np.sqrt(lam)
    
    return lam

def lam_e(n1,n2,m1,m2,Z1,Z2,T):
    
    #note - this assumes ion and electron temperatures are the same
    
    m_e = 9.109e-28        #g
    hbar = 6.5821e-16      #eV-s
    pi = np.pi
    erg_to_ev = 6.2415e11
    e2_cgs = 1.44e-7       #eV-cm
    
    mu = m1*m2/(m1 + m2)   #g
    M1 = m1/(m1 + m2)
    M2 = m2/(m1 + m2)
    
    
    n = n1 + n2            #1/cm^3
    n_e = Z1*n1 + Z2*n2
    
    x1 = n1/n
    x2 = n2/n
    
    #define screening length
    
    EF = hbar*hbar*(3.0*pi*pi*n_e)**(2.0/3.0) / (2.0*m_e) / erg_to_ev   #eV
    lam = 4*pi*e2_cgs*n_e/np.sqrt(T*T + 4.0*EF*EF/9.0)                  #1/cm^2, this is really 1/lam_e
    
    
    return lam

def lam_eff2(n1,n2,m1,m2,Z1,Z2,T):
    
    #note - this assumes ion and electron temperatures are the same
    
    m_e = 9.109e-28        #g
    hbar = 6.5821e-16      #eV-s
    pi = np.pi
    erg_to_ev = 6.2415e11
    e2_cgs = 1.44e-7       #eV-cm
    
    mu = m1*m2/(m1 + m2)   #g
    M1 = m1/(m1 + m2)
    M2 = m2/(m1 + m2)
    
    
    n = n1 + n2            #1/cm^3
    n_e = Z1*n1 + Z2*n2
    
    x1 = n1/n
    x2 = n2/n
    
    #define screening length
    
    EF = hbar*hbar*(3.0*pi*pi*n_e)**(2.0/3.0) / (2.0*m_e) / erg_to_ev   #eV
    lam_e = 4*pi*e2_cgs*n_e/np.sqrt(T*T + 4.0*EF*EF/9.0)                  #1/cm^2, this is really 1/lam_e
    
    a_1 = (3.0*Z1 /(4.0*pi*n_e) )**(1.0/3.0)
    lam_1 = 4.0*pi*Z1*Z1*e2_cgs*n1/T                                          #1/cm^2, this is reall 1/lam_1
    Gam1 = Z1*Z1*e2_cgs/a_1/T
    
    a_2 = (3.0*Z2 /(4.0*pi*n_e) )**(1.0/3.0)
    lam_2 = 4.0*pi*Z2*Z2*e2_cgs*n2/T                                          #1/cm^2
    Gam2 = Z2*Z2*e2_cgs/a_2/T
    
    
    lam = lam_e + lam_1/(1.0 + 3.0*Gam1) + lam_2/(1.0 + 3.0*Gam2)
    lam = 1.0/np.sqrt(lam)
    
    return lam

def gammaSM2(n1,n2,m1,m2,Z1,Z2,T,atot,kappa):
    """Computes the K_ij coefficient gamma for a binary mixture"""
    
    n = n1 + n2
    rhotot = Z1*n1 + Z2*n2
    
    if kappa == -1:
        
        lam = lam_eff2(n1,n2,m1,m2,Z1,Z2,T)
        
        gamma = Z1*Z2*e2/lam/T
    else:
        x1 = n1/n
        z1 = Z1*n1/rhotot
        x2 = n2/n
        z2 = Z2*n2/rhotot
        Gamma = Z1*Z2*e2/atot/T
        Gamma11 = Z1*Z1*e2/atot/T
        Gamma22 = Z2*Z2*e2/atot/T
        gamma = Gamma*np.sqrt( kappa**2 + 3.0*x1*Gamma11/(1.0 + 3.0*Gamma11*(x1/z1)**(1.0/3.0))
                              + 3.0*x2*Gamma22/(1.0 + 3.0*Gamma22*(x2/z2)**(1.0/3.0)) )
    return gamma

def mfp(n1,m1,Z1,T,kappa=-1):
    
    D=D_ij(n1,n1,m1,m1,Z1,Z1,T,kappa=-1)
    mred = m1*m1/(m1+m1)
    #    vth=2.02e-06*np.sqrt(T/(np.pi*mred))
    vth=np.sqrt(8*1.38e-23*T*11600/(np.pi*mred*1.e-3))
    return 3*D*1.e-4/vth

def Wigner_Seitz_radius(n):
    return (3./(4.*np.pi*n))**(1./3.)

def ICFAnalytical_solution(LammpsDens,LammpsCharges,LammpsTemperature):
    
    """Computes thermal conductivity, viscosity and mutual diffusion coefficients.
        Inputs: LammpsDens            - 1/cm^3
                LammpsCharges         - unitless
                LammpsTemperature     - eV
        
        Outputs: kappa, eta, D       - W/m/K; Pa.s; cm^2/ s
        """
    
    m=np.array([3.3210778e-24,6.633365399999999e-23,6.633365399999999e-23,6.633365399999999e-23])
    species_with_zeros_densities_index=[]
    species_with_non_zeros_densities_index=[]
    binary_case=[0,1]
    
    for i in binary_case:
        if LammpsDens[i]!=0.0:
            species_with_non_zeros_densities_index.append(i)
        else:
            species_with_zeros_densities_index.append(i)

    for i in species_with_non_zeros_densities_index:
        if len(species_with_non_zeros_densities_index)==2:
            conductivity_coefficient=Ktherm2(LammpsDens[0],LammpsDens[1],m[0],m[1],LammpsCharges[0],LammpsCharges[1],LammpsTemperature)
            viscosity_coefficient=eta2(LammpsDens[0],LammpsDens[1],m[0],m[1],LammpsCharges[0],LammpsCharges[1],LammpsTemperature)
            D_11=D_ij(LammpsDens[0],LammpsDens[0],m[0],m[0],LammpsCharges[0],LammpsCharges[0],LammpsTemperature,kappa=-1)
            D_12=D_ij(LammpsDens[0],LammpsDens[1],m[0],m[1],LammpsCharges[0],LammpsCharges[1],LammpsTemperature,kappa=-1)
            D_22=D_ij(LammpsDens[1],LammpsDens[1],m[1],m[1],LammpsCharges[1],LammpsCharges[1],LammpsTemperature,kappa=-1)
        
        for i in species_with_zeros_densities_index:
            if i==1:
                conductivity_coefficient = Ktherm1(LammpsDens[0],m[0],LammpsCharges[0],LammpsTemperature,kappa=-1)
                viscosity_coefficient = eta(LammpsDens[0],m[0],LammpsCharges[0],LammpsTemperature)
                D_11=D(LammpsDens[0],m[0],LammpsCharges[0],LammpsTemperature)
                D_12=0.0
                D_22=0.0
            else:
                conductivity_coefficient=Ktherm1(LammpsDens[1],m[1],LammpsCharges[1],LammpsTemperature,kappa=-1)
                viscosity_coefficient=eta(LammpsDens[1],m[1],LammpsCharges[1],LammpsTemperature)
                D_11=00
                D_12=0.0
                D_22=D(LammpsDens[1],m[1],LammpsCharges[1],LammpsTemperature)
    DifffusionCoefficients = [D_11, D_12, 0.0, 0.0, D_22, 0.0, 0.0, 0.0, 0.0, 0.0 ]
    return (conductivity_coefficient, viscosity_coefficient, DifffusionCoefficients)

def write_LammpsScript(Temperature,densities,charges,masses,system_index_species,box,cutoff,Teq,Trun,index_species,s_int,p_int,d_int, dirPrefix):
    
    """
    This script takes thermodynamical conditions of a plasma: temperature, densities, ionisation state (zbars), masses, together with the number of
    "of elements in the system, simulation box and cutoff sizes [in units of Wigner-Seitz radius], equilibration and production number steps, to generate a LAMMPS script file.
    
    Author: Abdou Diaw
        """
    nspec=system_index_species

    lammpsFName = os.path.join(dirPrefix, 'lammpsScript_'+str(nspec))
    with open(lammpsFName, 'w') as LammpsScript:
        
        
        # Once the zeros are removed estimte the number of species.
        #######################-----------------------------------------------#######################
        ## Estimate here parameters needed for the forces: screening length, force cutoff,
        ## time step, and drag frequency for thermostat.
        
        kb=       1.3807e-23
        hbar2=        1.1121811600000002e-68
        emass= 9.1094e-31
        eps0=8.8542e-12
        echarge= 1.6022e-19
        
        zbars=charges
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
        dtstep =    1./(300.*omega_p)
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
            csv_writer.writerow(['mass',s+1,1.e-3*masses[s]])

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
    
        csv_writer.writerow(['variable','s_int', 'equal', s_int])
        csv_writer.writerow(['variable','d_int', 'equal', d_int])
        csv_writer.writerow(['variable','p_int', 'equal', p_int])
        csv_writer.writerow(['variable','kb', 'equal', kb])
        csv_writer.writerow(['variable','T', 'equal', Temp1])
        csv_writer.writerow('')
        csv_writer.writerow(['variable','scale_factor_v', 'equal', '1./(${kb}*$T)*vol*${s_int}*dt'])
        csv_writer.writerow(['variable','scale_factor_k', 'equal', '${s_int}*dt/(${kb}*$T*$T)/vol'])
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

        csv_writer.writerow(['#---------','viscosity', 'calculations','---------#'])
        csv_writer.writerow('')

        s=0

        csv_writer.writerow(['fix',str(s+1+len(densities)),'all','ave/correlate',s_int,p_int,d_int,'&'])
        csv_writer.writerow(['v_pxy', 'v_pxz', 'v_pyz', 'type', 'auto', 'file', 'profile.stress.dat', 'ave', 'running'])
        csv_writer.writerow(['variable','v11','equal', 'trap(f_'+str(s+1+len(densities))+'[3]'+')'+'*${scale_factor_v}'])
        csv_writer.writerow(['variable','v22','equal', 'trap(f_'+str(s+1+len(densities))+'[4]'+')'+'*${scale_factor_v}'])
        csv_writer.writerow(['variable','v33','equal', 'trap(f_'+str(s+1+len(densities))+'[5]'+')'+'*${scale_factor_v}'])
        row_list.append('v_v11')
        row_list.append('v_v22')
        row_list.append('v_v33')

        csv_writer.writerow('')

        csv_writer.writerow(['#---------','conductivity', 'calculations','---------#'])
        csv_writer.writerow('')
        
        s=1
        csv_writer.writerow(['fix',str(s+1+len(densities)),'all','ave/correlate',s_int,p_int,d_int,'&'])
        csv_writer.writerow(['c_flux[1]', 'c_flux[2]', 'c_flux[3]', 'type', 'auto', 'file', 'profile.heatflux.dat', 'ave', 'running'])
        csv_writer.writerow(['variable','k11','equal', 'trap(f_'+str(s+1+len(densities))+'[3]'+')'+'*${scale_factor_k}'])
        csv_writer.writerow(['variable','k22','equal', 'trap(f_'+str(s+1+len(densities))+'[4]'+')'+'*${scale_factor_k}'])
        csv_writer.writerow(['variable','k33','equal', 'trap(f_'+str(s+1+len(densities))+'[5]'+')'+'*${scale_factor_k}'])
        row_list.append('v_k11')
        row_list.append('v_k22')
        row_list.append('v_k33')
        csv_writer.writerow('')
        
        csv_writer.writerow('')

        csv_writer.writerow(row_list)
        csv_writer.writerow('')

        csv_writer.writerow(['#---------','Viscosity','coefficients', 'in', 'cm^2/s','---------#'])
        csv_writer.writerow('')
        

        csv_writer.writerow(['variable','v','equal','(v_v11'+'+v_v22'+'+v_v33'+')'+'/3.'])

        csv_writer.writerow('')
        csv_writer.writerow(['#---------','Conductivities','coefficients', 'in', 'cm^2/s','---------#'])
        csv_writer.writerow('')


        csv_writer.writerow(['variable','k','equal','(v_k11'+'+v_k22'+'+v_k33'+')'+'/3.'])



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

        csv_writer.writerow(['print','v=${v'+'}','file','viscosity_coefficient.csv'])

        csv_writer.writerow(['print','k=${k'+'}','file','conductivity_coefficient.csv'])
        csv_writer.writerow('')
    return 'lammpsScript_'+str(nspec)


def check_zeros_trace_elements(Temperature,densities,charges,masses,box,cutoff,Teq,Trun,s_int,p_int,d_int,eps_traces, dirPrefix):
    species_with_zeros_densities_index=[]
    traces_elements_index =[]
    non_traces_elements_index=[]
    lammpsScripts = []

    for i in range(len(densities)):
        if densities[i]==0.0:
            species_with_zeros_densities_index.append(i)
            # Put a check here to make sure all the densities are not zeros. If that the case stop the simulations.
        elif densities[i]/sum(densities) < eps_traces:
                traces_elements_index.append(i)
        else:
            non_traces_elements_index.append(i)

    ## Build individual script for the trace elements.

    for s in traces_elements_index:
        dens=np.array([densities[s]])
        Z=np.array([charges[s]])
        m=np.array([masses[s]])
        b='single_'+str(s)+str(s)
        traceScript = write_LammpsScript(Temperature,dens,Z,m,b,box,cutoff,Teq,Trun,traces_elements_index,s_int,p_int,d_int, dirPrefix)
        lammpsScripts.append(traceScript)
    
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

    mixtureScript = write_LammpsScript(Temperature,densities[non_traces_elements_index],charges[non_traces_elements_index],masses[non_traces_elements_index],b,box,cutoff,Teq,Trun,non_traces_elements_index,s_int,p_int,d_int, dirPrefix)
    lammpsScripts.append(mixtureScript)

    return (species_with_zeros_densities_index, lammpsScripts)


def write_output_coeff(densities0,species_with_zeros_densities_index):
    # Use the results to build mutual_diffusion for trace and missing species. Darken.
    concentrations= densities0/sum(densities0)
    nspecies=np.arange(0,len(concentrations),1)
    
    ### Take all the self-diffusions values
    ### Also create viscosities files for the zero densities species
    
    
    
    d_ii= []
    for i in nspecies:
        for j in species_with_zeros_densities_index:
            with open('diffusion_coefficient_'+str(j)+str(i)+'.csv', 'w') as f:
                csv_writer = csv.writer(f,delimiter=' ')
                csv_writer.writerow(['D=0'])

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
                    csv_writer.writerow(['D='+str(concentrations[i]*d_ii[j]+concentrations[j]* d_ii[i])])

def icfComparator(lhs, rhs, epsilon):
    retVal = True
    if rhs.Temperature != 0.0 and (lhs.Temperature - rhs.Temperature) / rhs.Temperature > epsilon:
        retVal = False
    for i in range(4):
        if rhs.Density[i] != 0.0 and (lhs.Density[i] - rhs.Density[i]) / rhs.Density[i] > epsilon:
            return False
        if rhs.Charges[i] != 0.0 and (lhs.Charges[i] - rhs.Charges[i]) / rhs.Charges[i] > epsilon:
            return False
    return retVal