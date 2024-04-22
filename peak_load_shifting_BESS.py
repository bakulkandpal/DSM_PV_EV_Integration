from pyomo.environ import *
import numpy as np
import os
import matplotlib.pyplot as plt


def peak_shifting_bess(bess_capacity_kWh, charging_requirements, hourly_data, charger_power, num_buses, buses_time_range, pv_generation_15min, day_of_year, time_range1, time_range2, last_time_slot, case_pv):
    
    bess_power_kW = bess_capacity_kWh*0.5  # Maximum charge/discharge power rating in kW. Assumed charging/discharging efficiency 100% as of now.
    bess_initial_soc = 0.5 * bess_capacity_kWh  # Initial SOC assumed 50% of capacity. Can be dynamic also.
    
    def time_str_to_slot_index(time_str):
        hours, minutes = map(int, time_str.split(':'))
        return (hours - time_range1[0]) * 4 + minutes // 15  # Taking time_slot 12:00 as the base
    
    num_time_slots = time_str_to_slot_index(last_time_slot) + 1

    model = ConcreteModel()

    model.time_slots = RangeSet(0, num_time_slots-1)

    model.buses = RangeSet(0, len(buses_time_range) - 1)

    start_pv = day_of_year * 96 + time_range1[0]*4  
    end_pv = start_pv + num_time_slots  # Up to and including last time slot
    # pv_generation = {i - start_pv: pv_generation_15min[i] for i in range(start_pv, end_pv)}  # Use this for actual PV data.
    
    ebus_fixed = {i - time_range1[0]*4 : charging_requirements[i] for i in range(time_range1[0]*4, time_range1[0]*4+num_time_slots)} 
    
    pv_values = case_pv  # Use this for case studies.
    pv_generation = {i: pv for i, pv in enumerate(pv_values)}  # Use this for case studies.
    
    model.pv = Param(model.time_slots, initialize=pv_generation)
    model.charging_rate = Var(model.buses, model.time_slots, within=NonNegativeReals, bounds=(0, 240))
    model.energy_required = Param(model.buses, initialize={b: buses_time_range[b]['Energy Required (kWh)'] for b in range(len(buses_time_range))})
    model.ebus_fixed = Param(model.time_slots, initialize=ebus_fixed, within=NonNegativeReals, default=0)
    
    model.bess_charge_discharge = Var(model.time_slots, within=Reals, bounds=(-bess_power_kW, bess_power_kW))
    model.soc = Var(model.time_slots, within=NonNegativeReals, bounds=(0, bess_capacity_kWh))
    model.initial_soc = Constraint(expr=model.soc[0] == bess_initial_soc)
    
    def soc_final_rule(m):
        return m.soc[num_time_slots-1] == bess_initial_soc
    model.soc_final = Constraint(rule=soc_final_rule)
    
    def bess_discharge_limit_rule(m, t):
        return m.bess_charge_discharge[t] >= -sum(m.charging_rate[b, t] for b in m.buses)
    model.bess_discharge_limit = Constraint(model.time_slots, rule=bess_discharge_limit_rule)

    def soc_update_rule(m, t):
        if t == 0:
            return Constraint.Skip  
        return m.soc[t] == m.soc[t-1] + (m.bess_charge_discharge[t] * 0.25)  
    model.soc_update = Constraint(model.time_slots, rule=soc_update_rule)

    def energy_requirement_rule(m, b):
        start_time_str = buses_time_range[b]['Charging Start']
        start_slot = time_str_to_slot_index(start_time_str)
        last_slot = time_str_to_slot_index(last_time_slot)  # Cut-off time for all e-buses of first batch
        # return sum(m.charging_rate[b, t] * 0.25 for t in range(start_slot, last_slot + 1)) >= m.energy_required[b]
        return sum(m.charging_rate[b, t] * 0.25 for t in range(0, last_slot - 1)) == m.energy_required[b]
    model.energy_requirement = Constraint(model.buses, rule=energy_requirement_rule)
    
    def total_energy_balance_rule(m):
        total_energy_delivered = sum(m.charging_rate[b, t] * 0.25 for b in m.buses for t in m.time_slots)
        total_energy_required = sum(m.energy_required[b] for b in m.buses)
        return total_energy_delivered == total_energy_required
    model.total_energy_balance = Constraint(rule=total_energy_balance_rule)

    def no_charging_before_start_rule(m, b, t):
        start_slot = time_str_to_slot_index(buses_time_range[b]['Charging Start'])
        if t < start_slot:
            return m.charging_rate[b, t] == 0
        else:
            return Constraint.Skip  
    model.no_charging_before_start = Constraint(model.buses, model.time_slots, rule=no_charging_before_start_rule)
    
    def total_charging_demand_rule(m, t):
        return sum(m.charging_rate[b, t] for b in m.buses) == m.ebus_fixed[t]
    model.total_charging_demand = Constraint(model.time_slots, rule=total_charging_demand_rule)

    
    def objective_rule(m):
        # return sum((m.pv[t] - m.bess_charge_discharge[t])**2 for t in model.time_slots)
        return sum((m.pv[t] - m.bess_charge_discharge[t] - sum(m.charging_rate[b, t] for b in m.buses))**2 for t in m.time_slots)
    model.objective = Objective(rule=objective_rule, sense=minimize)


    solver_path = r'C:\Users\Bakul\Downloads\Ipopt-3.11.1-win64-intel13.1\Ipopt-3.11.1-win64-intel13.1\bin\ipopt.exe'
    solver = SolverFactory('ipopt', executable=solver_path)
    # solver = SolverFactory('gurobi')
    result = solver.solve(model, tee=True)

    print("Solver Status:", result.solver.status)
    print("Solver Termination Condition:", result.solver.termination_condition)
    
    bess_values = [value(model.bess_charge_discharge[t]) for t in model.time_slots]
    bess_soc = {t: value(model.soc[t]) for t in model.time_slots}
    
    charging_rates = {}
    for b in model.buses:
        for t in model.time_slots:
            if (b, t) in model.charging_rate:
                charging_rate_value = model.charging_rate[b, t].value
                if charging_rate_value is not None: #and charging_rate_value > 0:  
                    charging_rates[(b, t)] = charging_rate_value
                    
                    
    sum_energy_per_bus = {}
    sum_power_per_time_slot = {}
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
                        sum_power_per_time_slot[t] = 0
                    sum_energy_per_time_slot[t] += energy_kWh 
                    sum_power_per_time_slot[t] += charging_rate_value
                    
    times = list(pv_generation.keys())
    pv_values = [pv_generation[t] for t in times]
    ebus_values = [sum_power_per_time_slot.get(t, 0) for t in times]  
    
    end_time_str = last_time_slot
    end_hour, end_minutes = map(int, end_time_str.split(':'))
    
    time_labels = []
    current_hour = time_range1[0]
    current_minute = 0

    while current_hour < end_hour or (current_hour == end_hour and current_minute <= end_minutes):
        time_label = f"{current_hour:02d}:{current_minute:02d}"
        time_labels.append(time_label)
        current_minute += 15
        if current_minute >= 60:
            current_minute = 0
            current_hour += 1      
       
    
    plt.figure(figsize=(15, 6))
    plt.plot(time_labels, pv_values, label='PV Generation', marker='o', linestyle='-', linewidth=2)
    plt.plot(time_labels, ebus_values, label='E-Bus Charging', marker='x', linestyle='--', linewidth=2)
    plt.plot(time_labels, bess_values, label='BESS Charging/Discharging', marker='^', linestyle='-.', linewidth=2)
    plt.xlabel('Time of Day', fontsize=12, fontweight='bold')
    plt.ylabel('Power [kW]', fontsize=12, fontweight='bold')
    plt.title('PV Generation E-Bus Charging and BESS', fontsize=14, fontweight='bold')
    plt.xticks(time_labels, rotation=45) 
    plt.legend()
    plt.tight_layout()  
    plt.show()
                    
    return charging_rates, sum_energy_per_bus, sum_energy_per_time_slot                

        