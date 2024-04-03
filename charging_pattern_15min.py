import random
import math

def generate_charging_data_15min(num_buses, soc_first_batch, soc_second_batch, battery_capacity, charger_power, time_range1, time_range2, soc_required):
    charging_data = []
    hourly_data = {f"{hour:02d}:{minute:02d}": {"Incoming": [], "Outgoing": []} 
                   for hour in range(24) for minute in [0, 15, 30, 45]}
    
    # intervals = [f"{hour:02d}:{minute:02d}" for hour in range(time_range1[0], time_range1[1]) for minute in [0, 15, 30, 45]] + \
                # [f"{hour:02d}:{minute:02d}" for hour in range(time_range2[0], time_range2[1]) for minute in [0, 15, 30, 45]]    
        
    intervals_range1 = [f"{hour:02d}:{minute:02d}" for hour in range(time_range1[0], time_range1[1]) for minute in [0, 15, 30, 45]]
    intervals_range2 = [f"{hour:02d}:{minute:02d}" for hour in range(time_range2[0], time_range2[1]) for minute in [0, 15, 30, 45]]
   
    def add_buses_to_intervals(num_buses, intervals, charger_pow, soc_req, soc_rand):
        for _ in range(num_buses):
            bus_id = f"Bus_{random.randint(1, 2000):04d}"
            start_interval = random.choice(intervals)

            initial_soc = random.randint(soc_rand[0], soc_rand[1])
            final_soc = soc_req
            energy_needed = ((final_soc - initial_soc) / 100) * battery_capacity

            charging_duration_hours = energy_needed / charger_pow
            charging_duration_intervals = math.ceil(charging_duration_hours * 4)
            
            charging_data.append({
                "Bus ID": bus_id,
                "Charging Start": start_interval,
                "Initial SOC (%)": initial_soc,
                "Final SOC (%)": final_soc,
                "Total Energy Required (kWh)": energy_needed,
                "Charging Duration": charging_duration_intervals})
            
            hourly_data[start_interval]["Incoming"].append({"Bus ID": bus_id, "Energy Required (kWh)": energy_needed})
        
    add_buses_to_intervals(num_buses, intervals_range1, charger_power[0], soc_required[0], soc_first_batch)
    add_buses_to_intervals(num_buses, intervals_range2, charger_power[1], soc_required[1], soc_second_batch)

    return charging_data, hourly_data
