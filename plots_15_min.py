import pandas as pd
import numpy as np
from pyxlsb import open_workbook as open_xlsb
from charging_pattern_15min import generate_charging_data_15min
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import math


def read_xlsb(sheet_name):
    xlsb_file_path = 'LSO_Calculations v2.02b.xlsb'

    data = []    
    with open_xlsb(xlsb_file_path) as wb:    
        with wb.get_sheet(sheet_name) as sheet:
            for row in sheet.rows():
                row_values = [item.v for item in row]
                data.append(row_values)

    df = pd.DataFrame(data[1:], columns=data[0])
    
    return df

sheet_name = 'Feeder Data'

feeder_data_df = read_xlsb(sheet_name)

feeder_load = feeder_data_df.iloc[29:, 12].values

feeder_load_15min = np.repeat(feeder_load, 4)

class feeder_data_class:    
    def __init__(self, num_buses, soc_first_batch, soc_second_batch, battery_capacity, charger_power, num_chargers, day_of_year, time_range1, time_range2, soc_required):
        self.num_buses = num_buses
        self.soc_first_batch = soc_first_batch
        self.soc_second_batch = soc_second_batch
        self.battery_capacity = battery_capacity
        self.charger_power = charger_power
        self.num_chargers = num_chargers
        self.day_of_year = day_of_year
        self.time_range1 = time_range1
        self.time_range2 = time_range2
        self.soc_required = soc_required
        
    def plots_15_mins(self):
        
        charging_data, hourly_data = generate_charging_data_15min(self.num_buses, self.soc_first_batch, self.soc_second_batch, self.battery_capacity, self.charger_power, self.time_range1, self.time_range2, self.soc_required)
        
        arrivals = []
        departures = []
        times = []
        energy_requirements_individual = []
        energy_requirements = []
        #time_slots = [f"{hour:02d}:{minute:02d}" for hour in range(24) for minute in [0, 15, 30, 45]]
        #time_slots = [f"{hour:02d}:{minute:02d}" for hour in range(24) for minute in [0, 15, 30, 45]] + [f"{hour:02d}:{minute:02d}" for hour in range(8) for minute in [0, 15, 30, 45]]
        
        time_slots1 = [f"{hour:02d}:{minute:02d}" for hour in range(24) for minute in [0, 15, 30, 45]]
        time_slots2 = [f"{24 + hour:02d}:{minute:02d}" for hour in range(8) for minute in [0, 15, 30, 45]]  # Next day's time-slots till 8 AM (E-buses depart).
        
        time_slots=time_slots1+time_slots2
        
        initial_soc_individual = []
        for time_slot in time_slots:
            hour = int(time_slot.split(':')[0])
            if hour >= 24:
                continue 
            arrivals_count = len(hourly_data[time_slot]["Incoming"])
            departures_count = len(hourly_data[time_slot]["Outgoing"])
            energy_required = sum(bus["Energy Required (kWh)"] for bus in hourly_data[time_slot]["Incoming"])
            arrivals.append(arrivals_count)
            energy_requirements.append(energy_required)
            
            if time_slot in hourly_data and "Incoming" in hourly_data[time_slot]:
                for bus in hourly_data[time_slot]["Incoming"]:
                    times.append(time_slot)
                    energy_requirements_individual.append(bus["Energy Required (kWh)"])
    
                    if hour <= self.time_range1[1]:
                        initial_soc_percentage = self.soc_required[0] - ((bus["Energy Required (kWh)"] / self.battery_capacity) * 100)
                    else:
                        initial_soc_percentage = self.soc_required[1] - ((bus["Energy Required (kWh)"] / self.battery_capacity) * 100)
                        
                    initial_soc_individual.append(initial_soc_percentage)
                    
        time_indices = [time_slots.index(time) for time in times]       
        
        charging_buses = {}
        available_chargers = {time_slot: self.num_chargers for time_slot in time_slots}
        
        num_time_slots = len(time_slots)  # The total number of 15-minute time slots in one day
        
        charging_matrix = np.zeros((num_time_slots, self.num_buses*2))
        
        def time_slot_index(time_str):
            hour, minute = map(int, time_str.split(':'))
            return hour * 4 + minute // 15
        
        for bus_index, bus in enumerate(charging_data):
            start_time_slot = time_slot_index(bus["Charging Start"])
            energy_required = bus["Total Energy Required (kWh)"]
            
            if bus_index < len(charging_data) / 2:
                charger_power_for_bus = self.charger_power[0]
            else:
                charger_power_for_bus = self.charger_power[1]
                
            charging_duration_15min = math.ceil(energy_required / (charger_power_for_bus / 4))   
            for i in range(charging_duration_15min):
                if start_time_slot + i < num_time_slots:
                    charging_matrix[start_time_slot + i, bus_index] = 1     
            
        connected_buses_per_slot = np.sum(charging_matrix, axis=1)
        
        energy_requirement_per_slot = np.zeros(num_time_slots)
        overflow_buses = 0
        actual_buses_charged_per_slot = np.zeros(num_time_slots, dtype=int)
        
        def after_first_before_second(slot, first_range, second_range):
            slot_hour = int(slot.split(':')[0])
            return first_range[0] <= slot_hour < second_range[0]
        
        def after_second_range(slot, second_range):
            slot_hour = int(slot.split(':')[0])
            return slot_hour >= second_range[0]
        
        for i, slot in enumerate(time_slots):
            connected_buses = np.sum(charging_matrix[i]) + overflow_buses
            
            if after_first_before_second(slot, self.time_range1, self.time_range2):
                charger_power_for_slot = self.charger_power[0]
            elif after_second_range(slot, self.time_range2):
                charger_power_for_slot = self.charger_power[1]
            else:
                charger_power_for_slot = 0 
            
            buses_charged = min(connected_buses, self.num_chargers)
            actual_buses_charged_per_slot[i] = buses_charged
            energy_requirement_per_slot[i] = buses_charged * charger_power_for_slot if charger_power_for_slot else 0
            overflow_buses = max(0, connected_buses - self.num_chargers)
        
        
        combined_load_15min_day = feeder_load_15min[(self.day_of_year-1)*96:(self.day_of_year)*96 + 32] + energy_requirement_per_slot
        day_feeder_load = feeder_load_15min[(self.day_of_year-1)*96 : self.day_of_year*96 + 32]
        
        days_with_new_peaks_15min = []
        day_peak_original=[]
        day_peak_ebus=[]
        for day in range((len(feeder_load_15min) // 96)-2):  # 128 intervals. 96 per day for 15-minute time slots + 22 more time-slots for next day's morning.
            feeder_load_day_15min = feeder_load_15min[day*96:(day+1)*96+32]  
            combined_load_day_15min = feeder_load_day_15min + energy_requirement_per_slot  
            max_feeder_load = np.max(feeder_load_day_15min)
            max_combined_load = np.max(combined_load_day_15min)
            day_peak_original.append(max_feeder_load)
            day_peak_ebus.append(max_combined_load)
            if max(combined_load_day_15min) > max(feeder_load_day_15min):
                days_with_new_peaks_15min.append(day)
        
        months = ["January", "February", "March", "April", "May", "June", 
                  "July", "August", "September", "October", "November", "December"]
        month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        cumulative_days = pd.Series(month_days).cumsum()
        
        def find_month(day):
            for i, cul_days in enumerate(cumulative_days):
                if day < cul_days: 
                    return months[i]
        
        violations_per_month_15min = [find_month(day) for day in days_with_new_peaks_15min]
        violation_counts_15min = pd.Series(violations_per_month_15min).value_counts().reindex(months, fill_value=0)
        
        days_of_year = range(1, len(day_peak_original) + 1)  
        
      
        def convert_time_for_plot(slot):
            hour, minute = map(int, slot.split(":"))
            return f"{(hour - 24) % 24:02d}:{minute:02d}" if hour >= 24 else slot
        plot_time_slots = [convert_time_for_plot(slot) for slot in time_slots]
        
        
        # plt.figure(figsize=(15, 5))
        # ax1 = plt.gca()
        # soc_plot = ax1.scatter(time_indices, initial_soc_individual, color='green', alpha=0.8, s=40, marker='o', label='Arrival Time SOC (%)')
        # ax1.set_title(f'Individual E-Bus Charging Requirements ({self.battery_capacity} kWh Battery Capacity)')
        # ax1.set_xlabel('Time of Day')
        # ax1.set_ylabel('Arrival Time SOC (%)')
        # ax1.tick_params(axis='y', labelcolor='green')
        # ax2 = ax1.twinx()
        # energy_plot = ax2.scatter(time_indices, energy_requirements_individual, color='blue', alpha=0.8, s=40, marker='x', label='Energy Required (kWh)')
        # ax2.set_ylabel('Energy Required (kWh)')
        # ax2.tick_params(axis='y', labelcolor='blue')
        # lines, labels = ax1.get_legend_handles_labels()
        # lines2, labels2 = ax2.get_legend_handles_labels()
        # ax2.legend(lines + lines2, labels + labels2, loc='upper right')
        # plt.xticks(range(0, len(plot_time_slots), 4), plot_time_slots[::4], rotation=45)
        # ax1.xaxis.set_major_locator(ticker.MultipleLocator(6))
        # plt.tight_layout()
        # plt.show()        
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 8))  
        soc_plot = ax1.scatter(time_indices, initial_soc_individual, color='green', alpha=0.8, s=30, marker='o', label='Arrival Time SOC (%)')
        ax1.set_title(f'Individual E-Bus Charging Requirements ({self.battery_capacity} kWh Battery Capacity)', pad=20)  # pad increases space between title and plot
        ax1.set_xlabel('Time of Day')
        ax1.set_ylabel('Arrival Time SOC (%)')
        ax1.tick_params(axis='y')
        ax1.xaxis.set_major_locator(ticker.MultipleLocator(6))
        energy_plot = ax2.scatter(time_indices, energy_requirements_individual, color='blue', alpha=0.8, s=30, marker='x', label='Energy Required (kWh)')
        ax2.set_xlabel('Time of Day')
        ax2.set_ylabel('Energy Required (kWh)')
        ax2.tick_params(axis='y')
        ax2.xaxis.set_major_locator(ticker.MultipleLocator(6))
        ax2.margins(x=0.01)
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines, labels, loc='upper right')
        ax2.legend(lines2, labels2, loc='upper right')
        plt.subplots_adjust(hspace=0.5) 
        plt.setp(ax1, xticks=range(0, len(plot_time_slots), 8), xticklabels=plot_time_slots[::8])
        plt.setp(ax2, xticks=range(0, len(plot_time_slots), 8), xticklabels=plot_time_slots[::8])
        for label in ax2.get_xticklabels():
            label.set_rotation(45)  
        plt.tight_layout()
        plt.show()
    
        
        plt.figure(figsize=(15, 5))
        plt.plot(time_slots1, arrivals, label='Arrivals', marker='o', linestyle='-', color='blue')
        plt.title('E-Bus Arrivals', fontsize=12)
        plt.xlabel('Time of Day', fontsize=12)
        plt.xticks(range(0, len(time_slots1), 4), time_slots1[::4], rotation=45)
        plt.ylabel('Number of E-Buses', fontsize=12)
        plt.legend()
        plt.show() 
        
        plt.figure(figsize=(15, 5))
        plt.plot(time_slots, energy_requirement_per_slot, label='Energy Consumption', marker='o', linestyle='-', color='orange')
        plt.title('Total Energy Consumption at Any Time-Slot', fontsize=12)
        plt.xlabel('Time of Day', fontsize=12)
        plt.xticks(range(0, len(plot_time_slots), 4), plot_time_slots[::4], rotation=45)
        plt.ylabel('Energy (kWh)', fontsize=12)
        plt.legend()
        plt.show()
        
        
        plt.figure(figsize=(15, 15))
        plt.subplot(2, 1, 1)
        plt.plot(time_slots, connected_buses_per_slot, label='Connected E-Buses (Without No. of Charger Limit)', marker='o', linestyle='-', color='green')
        plt.title('Number of E-Buses Connected for Charging (WITHOUT Limit on Available Chargers)', fontsize=12)
        plt.xlabel('Time Slot', fontsize=12)
        plt.ylabel('Number of Connected E-Buses', fontsize=12)
        plt.xticks(range(0, len( plot_time_slots), 4),  plot_time_slots[::4], rotation=45)  # Showing every 4th time slot in x-ticks, less clutter.
        plt.legend()
        plt.subplot(2, 1, 2)
        plt.plot(time_slots, actual_buses_charged_per_slot, label='Connected E-Buses', marker='x', linestyle='-', color='red')
        plt.title('Number of E-Buses Connected for Charging (WITH Limit on Available Chargers)', fontsize=12)
        plt.xlabel('Time Slot', fontsize=12)
        plt.ylabel('Number of Connected E-Buses', fontsize=12)
        plt.xticks(range(0, len( plot_time_slots), 4),  plot_time_slots[::4], rotation=45)
        plt.legend()
        plt.show()
        
        
        plt.figure(figsize=(15, 6))
        plt.plot(time_slots, combined_load_15min_day, label='Combined Feeder and E-Bus Charging Load', marker='', linestyle='-', color='green')
        plt.plot(time_slots, day_feeder_load, label='Original Feeder Load', marker='', linestyle='-', color='blue')  # Adjusted linestyle to '-'
        plt.title(f'Combined Feeder and E-Bus Charging Load for Day {self.day_of_year}', fontsize=12)
        plt.xlabel('Time Slot', fontsize=12)
        plt.ylabel('Load (kW)', fontsize=12)
        plt.xticks(range(0, len( plot_time_slots), 4),  plot_time_slots[::4], rotation=45)
        plt.legend()
        plt.tight_layout()
        plt.show()
        
        plt.figure(figsize=(15, 6)) 
        plt.plot(days_of_year, day_peak_original, label='Original Feeder Peak Load', linestyle='-', color='blue')
        plt.plot(days_of_year, day_peak_ebus, label='Peak Load with E-Bus Charging', linestyle='-', color='red')
        plt.title('Daily Maximum Load')
        plt.xlabel('Day of the Year')
        plt.ylabel('Load (kW)')
        plt.legend() 
        plt.show()
        
        
        plt.figure(figsize=(12, 6))
        violation_counts_15min.plot(kind='bar', color='skyblue', alpha=0.7)
        plt.ylabel('Number of Days with Peak Increase', fontsize=12)
        plt.title('Number of Peak Increase in a Month Due to E-Bus Charging', fontsize=12)
        plt.xticks(rotation=45)
        plt.ylim(0, 32) 
        plt.show()     
        
        return energy_requirement_per_slot,feeder_load_15min
        