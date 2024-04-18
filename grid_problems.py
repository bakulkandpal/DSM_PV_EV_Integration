import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import math


def grid_problems_15min(charging_requirements, feeder_load_15min, xmer_capacity):
    
    indices_beyond_threshold = []
    indices_beyond_threshold_ebus = []

    for day in range((len(feeder_load_15min) // 96)-2):
        start_idx = day * 96
        end_idx = (day + 1) * 96 +32
        daily_load = feeder_load_15min[start_idx:end_idx]
        combined_load = daily_load + np.array(charging_requirements)
        daily_excess_indices = np.where(daily_load > xmer_capacity)[0] + start_idx
        daily_excess_indices_ebus = np.where(combined_load > xmer_capacity)[0] + start_idx
        indices_beyond_threshold.extend(daily_excess_indices.tolist())
        indices_beyond_threshold_ebus.extend(daily_excess_indices_ebus.tolist())
        
    indices_beyond_threshold = np.array(indices_beyond_threshold)
    indices_beyond_threshold_ebus = np.array(indices_beyond_threshold_ebus)
    
    day_indices_beyond_threshold = np.unique(indices_beyond_threshold // 96)
    day_indices_beyond_threshold_ebus = np.unique(indices_beyond_threshold_ebus // 96)
        
    days_of_year = np.arange(365)   
    capacity_exceeded = np.zeros(365)
    capacity_exceeded_ebus = np.zeros(365)
    capacity_exceeded[day_indices_beyond_threshold] = 1
    capacity_exceeded_ebus[day_indices_beyond_threshold_ebus] = 1    
        
    y_offset = 0.05 # To avoid datapoint overlap in figure
    
    # plt.figure(figsize=(15, 5))
    # plt.scatter(days_of_year, capacity_exceeded - y_offset, c='blue', label='Without E-Bus Charging', alpha=0.95, s=20)
    # plt.scatter(days_of_year, capacity_exceeded_ebus + y_offset, c='red', label='With E-Bus Charging', alpha=0.95, s=20)
    # plt.title(f'Days Exceeding Transformer Capacity [{xmer_capacity} kVA]', fontsize=14, fontweight='bold')
    # plt.xlabel('Day of the Year', fontsize=12, fontweight='bold')
    # plt.ylabel('Transformer Capacity Exceeded?', fontsize=12, fontweight='bold')
    # plt.yticks([0, 1], ['No', 'Yes'], fontsize=12)  
    # plt.ylim(-0.2, 1.2)  # To account for added offset
    # plt.legend(frameon=False, fontsize=12)
    # plt.show()
   
    
    return indices_beyond_threshold, indices_beyond_threshold_ebus, day_indices_beyond_threshold, day_indices_beyond_threshold_ebus

