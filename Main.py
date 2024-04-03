from plots_15_min import feeder_data_class
from grid_problems import grid_problems_15min
from load_flow_radial import perform_load_flow
from pv_analysis import demand_response_class
from charging_pattern_15min import generate_charging_data_15min
from peak_load_shifting import peak_shifting


day_of_year = 150  # For the visual plot of combined load of a particular day. 

########## Charging Depot Parameters
num_buses = 20  # Total number of E-buses to be charged in each batch. (Total 2 different batches)
charger_power = (240, 240)  # Charger capacity in kW. First and second value denote first and second batch charging power respectively.
num_chargers = 30  # Total number of chargers available at the station.
time_range1 = (12, 14)  # First set of hours, in between which, E-buses arrive.
time_range2 = (20, 22)  # Second set of hours, in between which, E-buses arrive.


####### Power Grid Parameters
transformer_capacity = 8500 # Assumed capacity of distribution transformer in kVA.
station_location_grid=15  # The node at which the charging station is located in the power grid.
network_plots=False  # Input 'True' if grid voltages are to be shown in Plots, else 'False'.


####### Battery State of Charge Parameters
trip_soc_expenditure = 50  # Approximate battery SOC used in single trip of E-bus.
battery_capacity = 240  # Battery capacity of single E-Bus in kWh.
soc_required = (100, 100)  # Target SOC levels (in %) for the two batches of E-buses.


###### PV Generator Parameters
pv_size = 2000  # Size of PV in kW. Assuming a PV is installed in the same feeder as the charging depot.
plots_pv = False  # Input 'True' if PV generation and its impact on feeder loads is to be shown in Plots, else 'False'.



####### Calling External Functions
soc_first_batch = (100-trip_soc_expenditure-5, 100-trip_soc_expenditure+5)  # Initial SOC for first batch of E-buses.
soc_second_batch = (soc_required[0]-trip_soc_expenditure-5, soc_required[0]-trip_soc_expenditure+5)  # Initial SOC for second batch of E-buses.
charging_requirements, feeder_load_15min = feeder_data_class(num_buses, soc_first_batch, soc_second_batch, battery_capacity, charger_power, num_chargers, day_of_year, time_range1, time_range2, soc_required).plots_15_mins() 
indices_feeder, indices_ebus, day_indices, day_indices_ebus = grid_problems_15min(charging_requirements, feeder_load_15min, transformer_capacity)
voltage, current = perform_load_flow(station_location_grid, plot=network_plots)  
demand_response = demand_response_class(charging_requirements, feeder_load_15min, pv_size, day_of_year, plots_pv)
pv_generation_15min, daily_net_load, day_pv_hourly = demand_response.optimized_asset()
charging_data, hourly_data = generate_charging_data_15min(num_buses, soc_first_batch, soc_second_batch, battery_capacity, charger_power, time_range1, time_range2, soc_required)
#dsm_solution = peak_shifting(hourly_data, charger_power[1],num_buses)