import numpy as np
from CompressibleFlowFunctions import *

##The double choke problem##

##Calculate the injection area required to choke the injector, and the needle valve effective diameter with the following flow values:
Po1        = 800 #psi
Po2        = 400 #psi
To         = 300 #Kelvin
Dopipe     = 3/8 #pipe outer diameter in inches
PipeT      = 0.049 #wall thickness in inches
gamma_ox   = 1.4
gamma_fuel = 1.24
mdot_t     = 200 #g/s
Mm_ox      = 32 #molar mass
Mm_fuel    = 28 #molar mass
Ru         = 8314.5
Y_ox       = 96/124
Y_fuel     = 1-Y_ox
Dhole      = 1/32 #inches

##Preliminary calculations
mdot_ox   = mdot_t*Y_ox/1000
mdot_fuel = mdot_t*Y_fuel/1000

Dpipe = Dopipe-2*PipeT
Dpipe   = Dpipe*0.0254
Apipe   = np.pi*Dpipe**2/4


## Part 1 ##: Calculate the injector area knowing the stagnation conditions at state 2
Rs_ox      = Ru/Mm_ox
Rs_fuel    = Ru/Mm_fuel
Astar_ox   = area_from_mass(Po2, To, Rs_ox, gamma_ox, mdot_ox)
Astar_fuel = area_from_mass(Po2, To, Rs_fuel, gamma_fuel, mdot_fuel)

## Part 1.1 ##: How many should each injector have knowing the hole size is 1/32"?
numholes_ox   = hole_numbers(Dhole,Astar_ox)
numholes_fuel = hole_numbers(Dhole*2,Astar_fuel)


## Part 2 ##: Assuming the back pressure Pb = Po2, and knowing the mass flow rate of each gas, determine the location of the NSW in the nozzle.
##This section was solved step by step, this is why some variables overwrite each other

Dpipe = Dopipe-2*PipeT
Aneedle_ox   = area_from_mass(Po1,To,Rs_ox,gamma_ox,mdot_ox)
Aneedle_fuel = area_from_mass(Po1,To,Rs_fuel,gamma_fuel,mdot_fuel)

#Consider the subsonic branch
M_ox   = mach_from_aratio_subsonic(Apipe,Aneedle_ox,gamma_ox)
M_fuel = mach_from_aratio_subsonic(Apipe,Aneedle_fuel,gamma_fuel)
P_ox   = p_from_pratio(Po1,gamma_ox,M_ox)
P_fuel = p_from_pratio(Po1,gamma_fuel,M_fuel)
#This branch produces static pressures much larger than Po2 which we consider to be the back pressure Pb, therefore the flow must have gone supersonic at some point
#Consider the supersonic branch
M_ox   = mach_from_aratio_supersonic(Apipe,Aneedle_ox,gamma_ox)
M_fuel = mach_from_aratio_supersonic(Apipe,Aneedle_fuel,gamma_fuel)
P_ox   = p_from_pratio(Po1,gamma_ox,M_ox)
P_fuel = p_from_pratio(Po1,gamma_fuel,M_fuel)
#The supersonic branch produces static pressure much smaller than Pb, therefore we consider the appearance of a NSW
M2_ox   = mach_after_shock(M_ox,gamma_ox)
M2_fuel = mach_after_shock(M_fuel,gamma_fuel)
P2_ox   = pstatic_after_shock(M_ox,gamma_ox,P_ox)
P2_fuel = pstatic_after_shock(M_fuel,gamma_fuel,P_fuel)
#We notice Pb is between the supersonic and subsonic solutions. This indicates the presence of a NSW somewhere in the diverging part of the nozzle
#Now, we must find the area ratio where the shock can exist
#we know Po1 and Po2, so we find the Mach number ahead of the shock:
M_ox         = mach_from_pressure_ratio(Po1, Po2, gamma_ox)
M_fuel       = mach_from_pressure_ratio(Po1, Po2, gamma_fuel)\
#Now that we know what the Mach number ahead of the shock is, we can find the cross sectional area using:
Aratio_ox   = ((gamma_ox+1)/2)**(-(gamma_ox+1)/(2*(gamma_ox-1)))*(1+(gamma_ox-1)/2*M_ox*M_ox)**((gamma_ox+1)/(2*(gamma_ox-1)))/M_ox
Aratio_fuel = ((gamma_fuel+1)/2)**(-(gamma_fuel+1)/(2*(gamma_fuel-1)))*(1+(gamma_fuel-1)/2*M_fuel*M_fuel)**((gamma_fuel+1)/(2*(gamma_fuel-1)))/M_fuel

Ashock_ox   = Astar_ox*Aratio_ox
Ashock_fuel = Astar_fuel*Aratio_fuel
