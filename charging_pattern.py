import random
import math

def generate_charging_data(num_buses, soc_lower, soc_upper, battery_capacity, charger_power):
    charging_data = []
    hourly_data = {hour: {"Incoming": [], "Outgoing": []} for hour in range(24)}
    
    for _ in range(num_buses):
        bus_id = f"Bus_{random.randint(1, 2000):04d}"
        charging_periods = ["12:00-13:00", "13:00-14:00", "21:00-22:00", "22:00-23:00"]
        incoming_time = random.choice(charging_periods).split('-')[0]
        incoming_hour = int(incoming_time.split(':')[0])

        initial_soc = random.randint(soc_lower, soc_upper)  # Ensure lower bound is less
        final_soc = 100
        energy_needed = ((final_soc - initial_soc) / 100) * battery_capacity

        # Calculate charging duration and outgoing hour
        hours_to_charge = energy_needed / charger_power
        outgoing_hour = incoming_hour + math.ceil(hours_to_charge)

        # Adjust outgoing_hour if it goes beyond 24-hour format
        if outgoing_hour >= 24:
            outgoing_hour -= 24

        # Append detailed charging data for each bus
        charging_data.append({
            "Bus ID": bus_id,
            "Charging Start Hour": incoming_hour,
            "Outgoing Hour": outgoing_hour,  # Now explicitly storing outgoing hour
            "Initial SOC (%)": initial_soc,
            "Final SOC (%)": final_soc,
            "Energy Consumed (kWh)": energy_needed
        })

        # Log incoming and outgoing buses in hourly data
        hourly_data[incoming_hour]["Incoming"].append({
            "Bus ID": bus_id,
            "Initial SOC (%)": initial_soc,
            "Energy Required (kWh)": energy_needed
        })

        for h in range(incoming_hour, incoming_hour + math.ceil(hours_to_charge)):
            hour = h % 24  # Use modulo for hour wrapping
            hourly_data[hour]["Outgoing"].append({
                "Bus ID": bus_id,
                "Final SOC (%)": final_soc
            })
    
    return charging_data, hourly_data
