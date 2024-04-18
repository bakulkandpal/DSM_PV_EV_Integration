import pandas as pd
import numpy as np
from pyxlsb import open_workbook as open_xlsb
from charging_pattern import generate_charging_data
import matplotlib.pyplot as plt


num_buses = 30  # Total number of E-buses to be charged in a day. (In 2 different slots)
day_of_year = 75  # For the visual plot of combined load of a particular day.
battery_capacity = 240  # Battery capacity of single E-Bus in kWh
xmer_capacity = 10000 # Assumed capacity of distribution transformer in kVA
charger_power = 100  # Charger capacity in kW


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

soc_upper = 80  # For creating random E-bus initial SOC when it arrives
soc_lower = 40  # For creating random E-bus initial SOC when it arrives

charging_data, hourly_data = generate_charging_data(num_buses, soc_lower, soc_upper, battery_capacity, charger_power)


arrivals = [len(hourly_data[hour]["Incoming"]) for hour in range(24)]
departures = [len(hourly_data[hour]["Outgoing"]) for hour in range(24)]
energy_requirements = [sum([bus["Energy Required (kWh)"] for bus in hourly_data[hour]["Incoming"]]) for hour in range(24)]
hours = list(range(24))


times = []
energy_requirements_individual = []

for hour in range(24):
    for bus in hourly_data[hour]["Incoming"]:
        times.append(hour)
        energy_requirements_individual.append(bus["Energy Required (kWh)"])

plt.figure(figsize=(10, 6))
plt.scatter(times, energy_requirements_individual, color='red', alpha=0.6)
plt.title('Individual E-Bus Charging Requirements')
plt.xlabel('Hour of the Day')
plt.ylabel('Energy Required (kWh)')
plt.xticks(hours) 
plt.show()


plt.figure(figsize=(14, 6))
plt.subplot(2, 1, 1)
plt.bar(hours, arrivals, width=0.4, label='Arrivals', align='center')
plt.bar(hours, departures, width=0.4, label='Departures', align='edge')
plt.title('Hourly E-Bus Arrivals')
plt.xlabel('Hour of the Day')
plt.ylabel('Number of Buses')
plt.legend()
plt.subplot(2, 1, 2)
plt.plot(hours, energy_requirements, label='Energy Required (kWh)', marker='o', linestyle='-', color='r')
plt.title('Hourly Energy Requirements for E-Bus Charging')
plt.xlabel('Hour of the Day')
plt.ylabel('Power Required (kW)')
plt.legend()
plt.tight_layout()
plt.show()


start_hour = (day_of_year - 1) * 24
end_hour = day_of_year * 24
daily_feeder_load = feeder_data_df.iloc[start_hour:end_hour, 12].values
combined_load = daily_feeder_load + np.array(energy_requirements)



plt.figure(figsize=(10, 6))
plt.plot(combined_load, label='Combined Load', marker='o')
plt.plot(daily_feeder_load, label='Original Feeder Load', marker='x')
plt.xlabel('Hour of Day')
plt.ylabel('Load [kW]')
plt.title(f'Original & E-Bus Load for Day {day_of_year}')
plt.xticks(ticks=np.arange(24), labels=[f'{hour}:00' for hour in range(24)], rotation=45)
plt.legend()
plt.tight_layout()
plt.show()

days_with_new_peaks = []

for day in range(len(feeder_load) // 24):
    feeder_load_day = feeder_load[day*24:(day+1)*24]
    
    combined_load_day = feeder_load_day + np.array(energy_requirements)
    
    if max(combined_load_day) > max(feeder_load_day):
        days_with_new_peaks.append(day)
                
months = ["January", "February", "March", "April", "May", "June", 
          "July", "August", "September", "October", "November", "December"]        
month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
cumulative_days = pd.Series(month_days).cumsum()       

def find_month(day):
    for i, cul_days in enumerate(cumulative_days):
        if day <= cul_days:
            return months[i]

violations_per_month = [find_month(day) for day in days_with_new_peaks]

violation_counts = pd.Series(violations_per_month).value_counts().reindex(months, fill_value=0)

plt.figure(figsize=(12, 6))
violation_counts.plot(kind='bar', color='skyblue', alpha=0.7)
plt.ylabel('Number of Days with Peak Increase')
plt.title('Monthly Peak Increase Due to E-Bus Charging')
plt.xticks(rotation=45)
plt.show()


indices_beyond_threshold = np.where(feeder_load > xmer_capacity)[0]
days = indices_beyond_threshold // 24  # Integer division to find the day
hours = indices_beyond_threshold % 24
day_hour_pairs = np.array(list(zip(days, hours)), dtype=[('day', int), ('hour', int)])


indices_beyond_threshold_ebus = np.where(combined_load > xmer_capacity)[0]
days_ebus = indices_beyond_threshold_ebus // 24  # Integer division to find the day
hours_ebus = indices_beyond_threshold_ebus % 24
day_hour_pairs_ebus = np.array(list(zip(days_ebus, hours_ebus)), dtype=[('day', int), ('hour', int)])