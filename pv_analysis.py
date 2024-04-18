import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv('pv_delhi.csv')

pv_hourly = df['electricity']
pv_15min = pv_hourly.repeat(4).reset_index(drop=True)

class demand_response_class:
    def __init__(self, charging_requirements, feeder_load_15min, pv_size, day_of_year, plots_pv):
        self.charging_requirements = charging_requirements
        self.feeder_load_15min = feeder_load_15min
        self.pv_size = pv_size
        self.day_of_year = day_of_year
        self.plot = plots_pv         

    def optimized_asset(self):         
        pv_generation_15min = pv_15min * self.pv_size
        daily_net_load = []
        for day in range((35040 // 96)-1):
            start_idx = day * 96
            end_idx = start_idx + 96 + 32
            daily_feeder_load = self.feeder_load_15min[start_idx:end_idx]
            daily_charging_requirements = self.charging_requirements
            combined_load = daily_feeder_load + daily_charging_requirements
            daily_net_load.append(combined_load - pv_generation_15min[start_idx:end_idx])
        daily_net_load = np.array(daily_net_load)    
        combined_load_15min_day = self.feeder_load_15min[(self.day_of_year-1)*96:(self.day_of_year-1)*96 + 128] + self.charging_requirements
        day_feeder_load = self.feeder_load_15min[(self.day_of_year-1)*96 : self.day_of_year*96 +32]
        pv_generation_selected = pv_generation_15min[(self.day_of_year-1)*96 : self.day_of_year*96 + 32].reset_index(drop=True)
        after_pv = self.charging_requirements - pv_generation_selected
        day_pv_hourly = pv_hourly[(self.day_of_year-1)*24 : self.day_of_year*24]
        
        time_labels = [f"{hour:02d}:{minute:02d}" for hour in range(24) for minute in [0, 15, 30, 45]] 
        time_labels2 = [f"{hour:02d}:{minute:02d}" for hour in range(24) for minute in [0, 15, 30, 45]]  + [f"{24 + hour:02d}:{minute:02d}" for hour in range(8) for minute in [0, 15, 30, 45]]
        
        def convert_time_for_plot(slot):
            hour, minute = map(int, slot.split(":"))
            return f"{(hour - 24) % 24:02d}:{minute:02d}" if hour >= 24 else slot
        plot_time_slots = [convert_time_for_plot(slot) for slot in time_labels2]
        
        if self.plot:
            plt.figure(figsize=(15, 6))
            plt.plot(time_labels, pv_generation_15min[(self.day_of_year-1)*96 : self.day_of_year*96], label='PV Generation', linestyle='-', color='blue')
            plt.title(f'PV Generation for Day {self.day_of_year}')
            plt.xlabel('Time of Day')
            plt.ylabel('PV Generation (kW)')
            plt.xticks(range(0, len(time_labels), 4), time_labels[::4], rotation=45)
            plt.legend()
            plt.show()
            
            plt.figure(figsize=(15, 6))
            plt.plot(time_labels2, self.charging_requirements, label='Charging Load', linestyle='-', color='blue')
            plt.plot(time_labels2, after_pv, label=f'Net Load After PV (of {self.pv_size} kW)', linestyle='--', color='red')
            plt.title(f'Load Profiles for Day {self.day_of_year}')
            plt.xlabel('Time of Day')
            plt.ylabel('Load (kW)')
            plt.xticks(range(0, len(plot_time_slots), 4), plot_time_slots[::4], rotation=45)
            plt.legend()
            plt.show()
        
        return pv_generation_15min, daily_net_load, day_pv_hourly
    