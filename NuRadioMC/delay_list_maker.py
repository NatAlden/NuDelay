import numpy as np
from NuRadioMC.SignalProp import propagation
from NuRadioMC.utilities import medium


# Defining refractive index
ice = medium.greenland_simple()

# Domain setup
ch0_pos = np.array([0, 0, -97.55])
ch1_pos = np.array([0, 0, -98.55])
ch2_pos = np.array([0, 0, -99.55])
ch3_pos = np.array([0, 0, -100.55])
channel_positions = [ch0_pos, ch1_pos, ch2_pos, ch3_pos]

pulserXY_pos = np.array([100, 0])

depth_scans = np.linspace(0, -120, 5)
delay_list = []
angle_list = []


prop = propagation.get_propagation_module('analytic')
rays = prop(ice, n_reflections = 0)

for depth in depth_scans:
    X,Y= pulserXY_pos
    pulser_pos = np.array([X, Y, depth])

    delays = []
    angles = []
    for ch in channel_positions:
        rays.set_start_and_end_point(ch, pulser_pos)
        rays.find_solutions()
        vector = rays.get_receive_vector(0)  # Get angle of incidence of the first solution
        in_vec_x, in_vec_y, in_vec_z = vector
        angle = np.arctan(in_vec_z/ in_vec_x)  # Calculate angle in radians
        traveltime = rays.get_travel_time(0)  # Get travel time of the first solution

        delays.append(round(traveltime, 4))  # Round to 4 decimal places
        angles.append(round(np.rad2deg(angle),4))
    delays = np.array(delays)  # Convert to nanoseconds
    delays-=np.min(delays)  # Normalize delays to the first channel
    delay_list.append(delays)
    angle_list.append(angles)
    print(depth, angle_list[-1], np.mean(angle_list[-1]), delay_list[-1])



"""
for iS in range(rays.get_number_of_solutions()):
    solution_type = propagation.solution_types[rays.get_solution_type(iS)]
    traveltime = rays.get_travel_time(iS)
    print(f"Solution {iS}: {solution_type}, Travel time: {traveltime:.2f} ns")

"""


