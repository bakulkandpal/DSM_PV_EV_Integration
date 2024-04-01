from pyomo.environ import *
import numpy as np

def peak_shifting(hourly_data, charger_power): 
    charging_efficiency = 0.9  
    time_slots = np.array([time for time in hourly_data])  
    num_time_slots = len(time_slots)  
    num_buses = len(set(entry['BusID'] for time_slot in hourly_data.values() for entry in time_slot['Incoming']))
    
    bus_availability = {bus_id: [] for bus_id in range(num_buses)}
    for time_slot, data in hourly_data.items():
        for entry in data['Incoming']:
            bus_id = entry['BusID']
            bus_availability[bus_id].append(time_slot)
    
    model = ConcreteModel()
    
    model.time_slots = Set(initialize=time_slots)
    model.buses = Set(initialize=range(num_buses))
    
    model.charging = Var(model.buses, model.time_slots, within=NonNegativeReals)
    
    def energy_requirement_rule(model, bus_id):
        required_energy = sum(entry['Energy Required (kWh)'] for time_slot in bus_availability[bus_id] 
                              for entry in hourly_data[time_slot]['Incoming'] if entry['BusID'] == bus_id)
        charged_energy = sum(model.charging[bus_id, time_slot] * charging_efficiency for time_slot in bus_availability[bus_id])
        return charged_energy >= required_energy
    
    model.EnergyRequirement = Constraint(model.buses, rule=energy_requirement_rule)
    
    def squared_load_rule(model):
        return sum((sum(model.charging[b, ts] for b in model.buses if ts in bus_availability[b]) + feeder_load_15min[ts])**2 for ts in model.time_slots)
    model.Objective = Objective(rule=squared_load_rule, sense=minimize)
    
    
    solver = SolverFactory('gurobi')
    results = solver.solve(model, tee=True)
    
    if (results.solver.status == SolverStatus.ok) and (results.solver.termination_condition == TerminationCondition.optimal):
        charging_schedule = pd.DataFrame(index=model.time_slots, columns=[f'Bus_{b}' for b in model.buses])
        for b in model.buses:
            for ts in model.time_slots:
                charging_schedule.at[ts, f'Bus_{b}'] = model.charging[b, ts].value
        print(charging_schedule)
    else:
        print("The problem is not solved to optimality.")
