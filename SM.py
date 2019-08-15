"""
This module computes single species and binary transport coefficients based on the paper of 
 L. G. Stanton and M. S. Murillo "Ionic transport in high-energy-density
matter", PRE ${\bf 93}$ 043203 (2016).  
"""

import numpy as np

e2 = 1.44e-7
pi = np.pi

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




def K11(g):
    if g < 1.0:
        return -0.25*np.log(1.466*g - 1.7836*g**2.0 + 1.4313*g**3.0 - 0.55833*g**4 + 0.061162*g**5)
    else:
        return (0.081033 - 0.091336*np.log(g) + 0.05176*np.log(g)**2)/(1.0 - 0.50026*g + 0.17044*g*g)

def K12(g):
    if g < 1.0:
        return -0.25*np.log(0.52094*g + 0.25153*g**2.0 - 1.1337*g**3.0 + 1.2155*g**4 - 0.43784*g**5)
    else:
        return (0.20572 - 0.16536*np.log(g) + 0.061572*np.log(g)**2)/(1.0 - 1.2770*g + 0.066993*g*g)

def K13(g):
    if g < 1.0:
        return -0.5*np.log(0.30346*g + 0.23739*g**2.0 - 0.62167*g**3.0 + 0.56110*g**4 - 0.18046*g**5)
    else:
        return (0.68375 - 0.384596*np.log(g) + 0.10711*np.log(g)**2)/(1.0 + 0.10649*g + 0.028760*g*g)

def K22(g):
    if g < 1.0:
        return -0.5*np.log(0.8541*g - 0.22898*g**2.0 - 0.60059*g**3.0 + 0.80591*g**4 - 0.30555*g**5)
    else:
        return (0.43475 - 0.21147*np.log(g) + 0.11116*np.log(g)**2)/(1.0 + 0.19665*g + 0.15195*g*g)

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

