from plots_15_min import feeder_data_class
from grid_problems import grid_problems_15min
from load_flow_radial import perform_load_flow
from pv_analysis import demand_response_class
from charging_pattern_15min import generate_charging_data_15min
from peak_load_shifting import peak_shifting


day_of_year = 150  # For the visual plot of combined load of a particular day. 

<<<<<<< HEAD
########## Charging Depot Parameters
num_buses = 30  # Total number of E-buses to be charged in each batch. (Total 2 different batches)
charger_power = (200, 80)  # Charger capacity in kW. First and second value denote first and second batch charging power respectively.
=======
########## Charging Station Parameters

num_buses = 20  # Total number of E-buses to be charged in each batch. (Total 2 different batches)
charger_power = (240, 40)  # Single charger capacity in kW. First and second value denote first and second batch charging power respectively.
>>>>>>> 3a61866e667b12af580f36fd2aefb5ddc810adae
num_chargers = 10  # Total number of chargers available at the station.
time_range1 = (12, 14)  # First set of hours, in between which, E-buses arrive.
time_range2 = (20, 22)  # Second set of hours, in between which, E-buses arrive.


####### Power Grid Parameters
transformer_capacity = 8500 # Assumed capacity of distribution transformer in kVA.
station_location_grid=15  # The node at which the charging station is located in the power grid.
network_plots=False  # Input 'True' if grid voltages are to be shown, else 'False'.


####### Battery State of Charge Parameters
soc_first_batch = (60, 70)  # Initial SOC for first batch of E-buses.
soc_second_batch = (60, 70)  # Initial SOC for second batch of E-buses.
battery_capacity = 240  # Battery capacity of single E-Bus in kWh.
soc_required = (80, 100)  # Target SOC levels (in %) for the two batches of E-buses.


###### PV Generator Parameters
pv_size = 2000  # Size of PV in kW. Assuming a PV is installed in the same feeder as the charging depot.



####### Calling External Functions
charging_requirements, feeder_load_15min = feeder_data_class(num_buses, soc_first_batch, soc_second_batch, battery_capacity, charger_power, num_chargers, day_of_year, time_range1, time_range2, soc_required).plots_15_mins() 
indices_feeder, indices_ebus, day_indices, day_indices_ebus = grid_problems_15min(charging_requirements, feeder_load_15min, transformer_capacity)
voltage, current = perform_load_flow(station_location_grid, plot=network_plots)  
demand_response = demand_response_class(charging_requirements, feeder_load_15min, pv_size, day_of_year)
pv_generation_15min, daily_net_load, day_pv_hourly = demand_response.optimized_asset()
charging_data, hourly_data = generate_charging_data_15min(num_buses, soc_first_batch, soc_second_batch, battery_capacity, charger_power, time_range1, time_range2, soc_required)
#dsm_solution = peak_shifting(hourly_data, charger_power[1],num_buses)