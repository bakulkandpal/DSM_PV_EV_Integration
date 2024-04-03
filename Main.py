from plots_15_min import feeder_data_class
from grid_problems import grid_problems_15min
from load_flow_radial import perform_load_flow
from pv_analysis import demand_response_class
from charging_pattern_15min import generate_charging_data_15min
from peak_load_shifting import peak_shifting


day_of_year = 150  # For the visual plot of combined load of a particular day. 

########## Charging Station Parameters

num_buses = 20  # Total number of E-buses to be charged in each batch. (Total 2 different batches)
charger_power = (240, 40)  # Single charger capacity in kW. First and second value denote first and second batch charging power respectively.
num_chargers = 10  # Total number of chargers available at the station.
time_range1 = (12, 14)  # First set of hours, in between which, E-buses arrive.
time_range2 = (20, 22)  # Second set of hours, in between which, E-buses arrive.

####### Power Grid Parameters

transformer_capacity = 8500 # Assumed capacity of distribution transformer in kVA.
station_location_grid=15  # The node at which the charging station is located in the power grid.
network_plots=False  # Input plot=True if grid voltages are to be shown, else False.

####### Battery State of Charge Parameters

soc_lower = 40  # For creating random E-bus initial SOC when it arrives.
soc_upper = 80  # For creating random E-bus initial SOC when it arrives.
battery_capacity = 240  # Battery capacity of single E-Bus in kWh.

###### PV Generator Parameters

pv_size = 2000  # Size of PV in kW.


####### Calling External Functions
charging_requirements, feeder_load_15min = feeder_data_class(num_buses, soc_lower, soc_upper, battery_capacity, charger_power, num_chargers, day_of_year, time_range1, time_range2).plots_15_mins() 
indices_feeder, indices_ebus, day_indices, day_indices_ebus = grid_problems_15min(charging_requirements, feeder_load_15min, transformer_capacity)
voltage, current = perform_load_flow(station_location_grid, plot=network_plots)  # Input plot=True if grid voltages are to be shown.
demand_response = demand_response_class(charging_requirements, feeder_load_15min, pv_size, day_of_year)
pv_generation_15min, daily_net_load, day_pv_hourly = demand_response.optimized_asset()
charging_data, hourly_data = generate_charging_data_15min(num_buses, soc_lower, soc_upper, battery_capacity, charger_power, time_range1, time_range2)
#dsm_solution = peak_shifting(hourly_data, charger_power[1])