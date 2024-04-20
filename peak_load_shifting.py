from pyomo.environ import *
import numpy as np
import os


def peak_shifting(hourly_data, charger_power, num_buses, buses_time_range, pv_generation_15min, day_of_year, time_range1, time_range2):
    def time_str_to_slot_index(time_str):
        hours, minutes = map(int, time_str.split(':'))
        return (hours - 12) * 4 + minutes // 15  # Convert from 12:00 as the base time

    model = ConcreteModel()

    model.time_slots = RangeSet(0, 13)  # Slots indexed from 0 to 13

    model.buses = RangeSet(0, len(buses_time_range) - 1)

    start_pv = day_of_year * 96 + time_range1[0]*4  # Start from 12:00 PM of the given day
    end_pv = start_pv + 14  # Up to and including 3:30 PM
    pv_generation = {i - start_pv: pv_generation_15min[i] for i in range(start_pv, end_pv)}
    
    model.pv = Param(model.time_slots, initialize=pv_generation)
    model.charging_rate = Var(model.buses, model.time_slots, within=NonNegativeReals, bounds=(0, 240))
    model.energy_required = Param(model.buses, initialize={b: buses_time_range[b]['Energy Required (kWh)'] for b in range(len(buses_time_range))})

    def energy_requirement_rule(m, b):
        start_time_str = buses_time_range[b]['Charging Start']
        start_slot = time_str_to_slot_index(start_time_str)
        last_slot = time_str_to_slot_index('15:30')  # Cut-off time for all e-buses
        # return sum(m.charging_rate[b, t] * 0.25 for t in range(start_slot, last_slot + 1)) >= m.energy_required[b]
        return sum(m.charging_rate[b, t] * 0.25 for t in range(0, last_slot - 1)) >= m.energy_required[b]
    model.energy_requirement = Constraint(model.buses, rule=energy_requirement_rule)

    def no_charging_before_start_rule(m, b, t):
        start_slot = time_str_to_slot_index(buses_time_range[b]['Charging Start'])
        if t < start_slot:
            return m.charging_rate[b, t] == 0
        else:
            return Constraint.Skip  
    model.no_charging_before_start = Constraint(model.buses, model.time_slots, rule=no_charging_before_start_rule)

    def objective_rule(m):
        return sum((m.pv[t] - sum(m.charging_rate[b, t] for b in m.buses if t in range(time_str_to_slot_index(buses_time_range[b]['Charging Start']), time_str_to_slot_index('15:30') + 1)))**2 for t in model.time_slots)
    model.objective = Objective(rule=objective_rule, sense=minimize)


    solver_path = r'C:\Users\Bakul\Downloads\Ipopt-3.11.1-win64-intel13.1\Ipopt-3.11.1-win64-intel13.1\bin\ipopt.exe'
    solver = SolverFactory('ipopt', executable=solver_path)
    result = solver.solve(model, tee=True)

    print("Solver Status:", result.solver.status)
    print("Solver Termination Condition:", result.solver.termination_condition)
    
    charging_rates = {}
    for b in model.buses:
        for t in model.time_slots:
            if (b, t) in model.charging_rate:
                charging_rate_value = model.charging_rate[b, t].value
                if charging_rate_value is not None: #and charging_rate_value > 0:  
                    charging_rates[(b, t)] = charging_rate_value
                    
                    
    sum_energy_per_bus = {}
    sum_energy_per_time_slot = {}

    for b in model.buses:
        sum_energy_per_bus[b] = 0  
        for t in model.time_slots:
            if (b, t) in model.charging_rate:
                charging_rate_value = value(model.charging_rate[b, t]) 
                if charging_rate_value is not None:  
                    energy_kWh = charging_rate_value * 0.25  
                    sum_energy_per_bus[b] += energy_kWh
                    if t not in sum_energy_per_time_slot:
                        sum_energy_per_time_slot[t] = 0
                    sum_energy_per_time_slot[t] += energy_kWh                 
                    
    return charging_rates, sum_energy_per_bus, sum_energy_per_time_slot                

        