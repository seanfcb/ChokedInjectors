import numpy as np
import sys
from scipy.optimize import bisect

###All functions take as an input: pressure in PSI, Temperature in Kelvin, Pipe diameters in inches
###All functions output answers in SI units

def fanno_losses(mdot,Rs,SG,Dpipe,Apipe,Po1,Po1_metric,To,gamma,mu,epsilon,L):
    ##==================================================================##
    ##============================PART 1================================##
    ##==================================================================##
    #Calculate the Mach number at the inlet of the pipe.
    ##==================================================================##
    M1  = bisect(delta_mass_stag,0.0001,0.99,args=(mdot,Po1_metric,Rs,To,gamma,Apipe))
    ##==================================================================##
    #Calculate the Fanning friction factor
    ##==================================================================##
    P1         = p_from_pratio(Po1,gamma,M1)
    Ti         = T_from_Tratio(To,gamma,M1)
    rhoi       = P1*(101325/14.7)/(Ti*Rs)
    Re         = rhoi*M1*np.sqrt(gamma*Rs*Ti)*Dpipe/mu
    darcy      = bisect(colebrook_white,1e-6,1,args=(Re,Dpipe,epsilon))
    fanning    = darcy/4


    # tabular_print("Location","P_static","P_total","Mach number","Lstar")
    # tabular_print("At the dip-stick inlet",round(P1,2),round(Po1_initial,2),round(M1,4))

    ##==================================================================##
    #Check that PHI(M1) > 4fL/D and calculate PHI(M2) if possible
    ##==================================================================##
    fanno_constant = 4*fanning*L/Dpipe
    PHI1           = fanno_equation(M1,gamma)
    if PHI1 < fanno_constant:
        #print(tabulate(print_statements))
        sys.exit("This pipe will choke before the next flow device")
    else:
        PHI2 = PHI1 - fanno_constant

    ##==================================================================##
    #Calculate Po2/Po1 using 2.3
    #Return Po2 & M2
    ##==================================================================##
    Lstar1   = Lstar_fanno(fanning,Dpipe,M1,gamma)
    L_int   = Lstar1 - L
    M2      = mach_fanno(L_int,fanning,Dpipe,gamma)
    print(M1, M2)
    Poratf  = fanno_po_ratio(M1,gamma)
    Postar  = Po1/Poratf
    Po2     = Postar*fanno_po_ratio(M2,gamma)
    P2      = p_from_pratio(Po2,gamma,M2)
    #tabular_print("Before bottle valve",round(P2,2),round(Po2,2),round(M2,4),Lstar1)

    return P1, Po1, M1, Lstar1, P2, Po2, M2, Re


def valve_losses(P1,Cv,SG,Q,mdot,Rs,To,gamma,Apipe):
    #P2 = bisect(flowrates, 0, P1,args=(P1,Cv,SG,Q))
    P2 = bisect(flowrates,0,P1,args=(P1,Cv,SG,Q))
    M_aval  = bisect(delta_mass_static,0.0001,0.99,args=(mdot,P2*101325/14.7,Rs,To,gamma,Apipe))
    Po_aval = P2/(1+((gamma-1)/2)*M_aval**2)**(-(gamma)/(gamma-1))
    return P2,M_aval,Po_aval

def flowrates(P2,P1,Cv,SG,Q):#(P2,P1,Cv,SG,Q):
    # Kappa = Q*np.sqrt(SG)/(42.2*Cv)
    # return np.sqrt(P1**2-Kappa**2)
    '''
    Expected inputs:
    P1 and P2: Pressures upstream and downstream, PSI
    Cv       : Flow coefficient
    SG       : Specific gravity w.r.t. air
    Q        : Volumetric flow rate, SCFH (see mdot_to_scfh)
    '''
    return 42.2*Cv*np.sqrt((P1-P2)*(P1+P2))/np.sqrt(SG) - Q ##From the Deltrol catalog, equation relating volume flow rate Q to

def area_from_mass(Po,To,Rs,gamma,mdot):
    """Function calculates the choking area using the compressible area ratio"""
    Gstar = Po*np.sqrt(gamma/Rs/To)*((gamma+1)/2)**(-(gamma+1)/(2*(gamma-1)))##We call Gstar the ratio mdot/Astar
    Astar = mdot/Gstar
    return Astar

def mass_from_area(M,Po,To,Rs,gamma,Area):
    ##Function calculates the mass flow rate using the compressible area ratio
    #Astar = np.pi*Dpipe*Dpipe/4
    #Gstar = Po*np.sqrt(gamma/Rs/To)*((gamma+1)/2)**(-(gamma+1)/(2*(gamma-1)))##We call Gstar the ratio mdot/Astar
    Gstar = Po*np.sqrt(gamma/Rs/To)*M*(1+(gamma-2)/2*M*M)**(-(gamma+1)/(2*(gamma-1)))##We call Gstar the ratio mdot/Astar
    mdot  = Gstar*Area
    return mdot

def prat_from_mach(gamma,M):
    ##For a known pre-shock mach number, what is the stagnation pressure ratio
    pratio = (((gamma+1)*M*M)/((gamma-1)*M*M+2))**(gamma/(gamma-1))*((gamma+1)/(2*gamma*M*M-(gamma-1)))**(1/(gamma-1))
    return pratio

def mach_from_pressure_ratio(Po1,Po2,gamma):
    ##For a desired stagnation pressure ratio, this function calculates the Mach number before a NSW
    Por  = Po2/Po1 ##Desired pressure ratio
    def Prat(Mi,gamma,Por):
        return (((gamma+1)*Mi*Mi)/((gamma-1)*Mi*Mi+2))**(gamma/(gamma-1))*((gamma+1)/(2*gamma*Mi*Mi-(gamma-1)))**(1/(gamma-1)) - Por
    M = bisect(Prat,1,100,args=(gamma,Por))
    return M

def mach_after_shock(M1,gamma):
    ##Calculates the Mach number after a NSW knowing the pre-shock Mach number
    M2 = np.sqrt(((gamma-1)*M1*M1+2)/(2*gamma*M1*M1-(gamma-1)))
    return M2

def pstatic_after_shock(M,gamma,P):
    ##Calculates the static pressure after a NSW knowing the pre-choke Mach number, gamma, and static pressure
    P2 = P*(2*gamma*M*M-(gamma-1))/(gamma+1)
    return P2

def pstag_after_shock(M,gamma,Po1):
    ##Calculates the stagnation pressure after a NSW knowing the pre-choke Mach number, gamma
    Po2 = Po1*(((gamma+1)*M*M)/((gamma-1)*M*M+2))**(gamma/(gamma-1))*((gamma+1)/(2*gamma*M*M-(gamma-1)))**(1/(gamma-1)) ##Solution from the NSW stagnation pressure ratio equation.
    return Po2

def astar_all_else_known(Dpipe,M,gamma):
    ##Function calculates the choking area using the compressible area ratio knowing all other properties
    Apipe  = np.pi*Dpipe**2/4
    Aratio = aratio_from_mach(M,gamma)
    Astar  = Apipe/Aratio
    Dstar  = np.sqrt(Astar*4/np.pi)
    return Astar, Dstar

def mach_from_G(Po,Rs,To,gamma,mdot,Dpipe,subsuper):
    Apipe = np.pi*Dpipe*Dpipe/4
    def delta_G(M,Po,Rs,To,gamma,mdot,Apipe):
        return mdot/Apipe - Po*np.sqrt(gamma/Rs/To)*M*(1+(gamma-2)/2*M*M)**(-(gamma+1)/(2*(gamma-1)))
    if subsuper == 'subsonic':
        M = bisect(delta_G,0.00001,0.99,args=(Po,Rs,To,gamma,mdot,Apipe))
    elif subsuper == 'supersonic':
        M = bisect(delta_G,1,99,args=(Po,Rs,To,gamma,mdot,Apipe))
    else:
        sys.exit('Please specify whether you want to resolve to the "subsonic" or "supersonic" branch when calling mach_from_G')

    return M

def mach_from_aratio(Aexit,Astar,gamma,subsuper):
    ##Function calculates the Mach number at a given location using the compressible area ratio knowing all other properties
    Apipe   = Aexit
    def arat_delta(M,gamma,Apipe,Astar):
        return Apipe/Astar - aratio_from_mach(M,gamma)
    if subsuper == 'subsonic':
        M = bisect(arat_delta,0.00001,0.99,args=(gamma,Apipe,Astar))
    elif subsuper == 'supersonic':
        M = bisect(arat_delta,1,99,args=(gamma,Apipe,Astar))
    else:
        sys.exit('Please specify whether you want to resolve to the "subsonic" or "supersonic" branch when calling mach_from_aratio')
    return M

def mach_from_massflow(Aexit,mdot,Po,To,Rs,gamma,subsuper):
    ##Function calculates the Mach number at a given location using the compressible area ratio knowing all other properties
    Apipe   = Aexit
    Dpipe   = np.sqrt(4*Apipe/np.pi)
    def g_delta(M,Po,To,Rs,gamma,Dpipe,Apipe,mdot):
        return mdot/Apipe - mass_from_area(M,Po,To,Rs,gamma,Dpipe)
    if subsuper == 'subsonic':
        M = bisect(g_delta,0.00001,0.99,args=(Po,To,Rs,gamma,Dpipe,Apipe,mdot))
    elif subsuper == 'supersonic':
        M = bisect(g_delta,1,99,args=(Po,To,Rs,gamma,Dpipe,Apipe,mdot))
    else:
        sys.exit('Please specify whether you want to resolve to the "subsonic" or "supersonic" branch when calling mach_from_massflow')

    return M

def aratio_from_mach(M,gamma):
    #Function calculates the compressible area ratio A/Astar knowing the Mach number and gamma
    Aratio = ((gamma+1)/2)**(-(gamma+1)/(2*(gamma-1)))*(1+(gamma-1)/2*M*M)**((gamma+1)/(2*(gamma-1)))/M
    return Aratio

def p_from_pratio(Po,gamma,M):
    ##Function calculates the static pressure knowing the gas properties, Mach number, and stagnation pressure using the isentropic pressure ratio equation P/Po
    P_static = Po*(1+((gamma-1)/2)*M**2)**(-(gamma)/(gamma-1))
    return P_static

def T_from_Tratio(To,gamma,M):
    ##Function calculates the static pressure knowing the gas properties, Mach number, and stagnation pressure using the isentropic pressure ratio equation P/Po
    T_static = To/(1+((gamma-1)/2)*M**2)
    return T_static

def mdot_to_scfh(mdot,Rs,G):
    mdot = mdot*60*2.205/1000 #g/s to lbm/min
    rho  = 101325/(Rs*288.7)*2.205/(3.28084**3) #calculate the stp density, converting to lb/cu.ft
    Q    = mdot/rho
    scfh = Q/np.sqrt(1/G)*60
    return scfh

def hole_numbers(Dhole,Astar):
    numholes = 4*Astar/np.pi/Dhole/Dhole
    return numholes

def colebrook_white(f,Re,D,epsilon):
    '''
    Subtracts both sides of the Colebrook-White equation to calculate the Darcy friction factor.
    Divide the result by 4 for the Fanning friction factor.
    Expected inputs:
    f       : Darcy friction factor
    Re      : Reynolds Number
    D       : Pipe diameter
    epsilon : Surface roughness in micrometers
    '''
    return 1/np.sqrt(f) - (-2)*np.log10(epsilon/(3.7*D) + 2.51/(Re*np.sqrt(f)))
def fanno_equation(M,gamma):
    return ((1-M**2)/(gamma*M**2) + (gamma+1)/(2*gamma)*np.log(((gamma+1)*M**2)/(2*(1+(gamma-1)/2*M**2))))
def delta_fanno(M,L,f,D,gamma):
    return ((1-M**2)/(gamma*M**2) + (gamma+1)/(2*gamma)*np.log(((gamma+1)*M**2)/(2*(1+(gamma-1)/2*M**2))))-4*f*L/D

def Lstar_fanno(f,D,M,gamma): #Define the Fanno equation to iterate on
    #return (D/(4*f))*((1-M**2)/(gamma*M**2)+(gamma+1)/(2*gamma)*np.log(((gamma+1)*M**2)/(2*(1+(gamma-1)/2*M**2))))
    return ((1-M**2)/(gamma*M**2) + (gamma+1)/(2*gamma)*np.log(((gamma+1)*M**2)/(2*(1+(gamma-1)/2*M**2))))*D/(4*f)

def mach_fanno(L,f,D,gamma): #Define the Fanno equation to iterate on
    M = bisect(delta_fanno,0.001,0.99,args=(L,f,D,gamma))
    return M

def delta_mass_static(M,mdot,P,Rs,To,gamma,A):
    return mdot/1000 - P*(1+(gamma-1)/2*M*M)**(gamma/(gamma-1))*A*np.sqrt(gamma/(Rs*To))*M*(1+(gamma-1)/2*M*M)**(-(gamma+1)/(2*(gamma-1)))

def delta_mass_stag(M,mdot,Po,Rs,To,gamma,A):
    '''
    expected inputs:
    mdot in g/s
    Po   in Pa
    '''
    return mdot/1000 - A*Po*np.sqrt(gamma/(Rs*To))*M*(1+(gamma-1)/2*M*M)**((-(gamma+1))/(2*(gamma-1)))

def fanno_po_ratio(M,gamma):
    return (1/M)*((2+(gamma-1)*M**2)/(gamma+1))**((gamma+1)/(2*(gamma-1)))
