from pyomo.environ import *
import numpy as np

def peak_shifting(hourly_data, charger_power, num_buses, buses_time_range, pv_generation_15min): 
    charging_efficiency = 0.95  
    time_slots = np.array([time for time in hourly_data])  
    num_time_slots = len(time_slots)  
    #num_buses = len(set(entry['BusID'] for time_slot in hourly_data.values() for entry in time_slot['Incoming']))
    
    bus_availability = {}
    
    for time_slot, data in hourly_data.items():
        for entry in data['Incoming']:
            bus_id = entry.get('BusID')
            if bus_id:
                if bus_id not in bus_availability:
                    bus_availability[bus_id] = []
                bus_availability[bus_id].append(time_slot)     
    
    def time_str_to_slot_index(time_str):
        hours, minutes = map(int, time_str.split(':'))
        time_slot_index = hours * 4 + minutes // 15
        return time_slot_index

    def calculate_end_time_slot(start_time_str):
        start_slot = time_str_to_slot_index(start_time_str)
        end_slot = start_slot + 8  # Adding 8 time slots to cover a 2-hour window
        return end_slot
    
    model = ConcreteModel()
    
    # Assuming buses_time_range is populated appropriately
    model.buses = RangeSet(0, len(buses_time_range) - 1)
    
    # Charging rate variable for each bus for each time slot within their 2-hour window
    model.charging_rate = Var(model.buses, within=NonNegativeReals, bounds=(0, 240))
    
    # Define a constraint for energy requirements
    def energy_requirement_rule(m, b):
        start_time_str = buses_time_range[b]['Charging Start']
        start_slot = time_str_to_slot_index(start_time_str)
        end_slot = calculate_end_time_slot(start_time_str)
        end_slot = min(end_slot, max(model.time_slots))  # Ensure it does not exceed available time slots
        return sum(m.charging_rate[b, t] * (1/4) for t in model.time_slots if start_slot <= t <= end_slot) >= buses_time_range[b]['Energy Required (kWh)']
    model.energy_requirement = Constraint(model.buses, rule=energy_requirement_rule)

    
    model.pv = Param(model.time_slots, initialize={t: 50 for t in range(96)})  # Example data
    
    def objective_rule(m):
        return sum((m.pv[t] - sum(m.charging_rate[b, t] for b in m.buses if t in range(time_str_to_slot_index(buses_time_range[b]['Charging Start']), calculate_end_time_slot(buses_time_range[b]['Charging Start']) + 1)))**2 for t in m.time_slots)
    
    model.objective = Objective(rule=objective_rule, sense=minimize)
    
    # Setup and solve the model
    solver = SolverFactory('glpk')
    result = solver.solve(model)
