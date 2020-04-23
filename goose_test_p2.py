#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Binary version of the test file (generic)
It runs all the other tests
Should do the same thing as the jupyter notebook
Created on Mon Mar  2 14:56:09 2020

@author: Andrey Chuhutin
"""

import pandas as pd
import datetime as dt
import numpy as np
#import time
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import configparser, os
#import re
#import pendulum

# this is definition whether we take into account timed values or not
# Is there a reason to use not timed values
is_timed = True

species_names = ["barnacle", "greylag", "pinkfoot"]
geese_foods = ['grain', 'grass', 'maize']
if is_timed==True:
    is_timed_str = '_timed'
else:
    is_timed_str = ''
    

# Let us define a mask that allows for all the fields to pass the filter if asterisk is used
# Here we assume that our data does not have asterisks, otherwise another symbol should be used
def ac_mask(df, key, value):
      if  value == '*':
          return df
      else:
          return df[df[key] == value] 
# The same mask as previously, but allows to merge the values together, uses pd.Series
# also faster than the previous one
def ac_mask_mult(df, key, value):
      if  value == '*':
          return df
      else:
          if not(isinstance(value, list)):
              value = [value]
          return df[pd.Series(df[key]).isin(value)]
          
# We will use this mask instead of a standard one
pd.DataFrame.mask = ac_mask_mult

data_dir = "rundir/"#"~/CLionProjects/GooseTests/run-directory1/"
#source_dir = #"~/CLionProjects/ALMaSS_all"
field_dir ="fielddir"#"~/CLionProjects/GooseTests/ALMaSS_inputs"
# let us read the config data, it will be useful afterwards
CONFIG_PATH=data_dir+'TIALMaSSConfig.cfg'
with open(os.path.expanduser(CONFIG_PATH), 'r') as f:
    config_string = '[dummy_section]\n' + f.read()
config = configparser.ConfigParser(strict=False)
config.read_string(config_string)

simulation_start_date = dt.date(2009, 1, 1)# we should check again that this is a right date, probably should be read from somewhere
simulation_start_date_ordinal=dt.date.toordinal(simulation_start_date)
my_dateparser=(lambda x: pd.to_datetime(x,unit='D', origin=simulation_start_date))


### Weight development
weight_data=pd.read_csv(data_dir+"GooseWeightStats.txt", sep='\t', header=0, dtype={'day': np.int16})
weight_data['daydate']=my_dateparser(weight_data['day'])
weight_data['week']=weight_data.daydate.dt.week
weight_data=weight_data[weight_data.iloc[:,5]>0 ]
field_data = pd.read_csv(field_dir+"/GooseManagement/Vejlerne/APIdata.txt", sep='\t', header=0, parse_dates=[0])
# we will change the field data into 2010-2011 seazon just to present them together nicely
field_data['weekdate']=np.array([i.strftime('%U') for i in field_data['Date']]).astype(int)
idx1=field_data['weekdate']>20
field_data.loc[idx1,'Date']=field_data[idx1]['Date'].apply(lambda dt:dt.replace(year=2010))
field_data.loc[np.logical_not(idx1),'Date']=field_data[np.logical_not(idx1)]['Date'].apply(lambda dt:dt.replace(year=2011))


fig9, ax9 = plt.subplots(1,3)

months = mdates.MonthLocator()
myFmt = mdates.DateFormatter('%b')
# plt.sca()
fig9.autofmt_xdate(rotation='vertical')
for i in range(3):
    ax9[i].xaxis.set_major_formatter(myFmt)
    ax9[i].grid()           
    ax9[i].xaxis.set_minor_locator(months)
    ax9[i].xaxis_date()
    temp_data = weight_data[weight_data['species']==species_names[i]]
    line9=ax9[i].errorbar(temp_data['daydate'],temp_data['mean_weight'],temp_data['mean_weight_sd'], capsize=3, ms=5, marker=".")
    ax9[i].set_title(species_names[i])


# Let us compare the field data and the simulation
fig10, ax10 = plt.subplots()
months = mdates.MonthLocator()
myFmt = mdates.DateFormatter('%b')
# plt.sca()
fig10.autofmt_xdate(rotation='vertical')
ax10.xaxis.set_major_formatter(myFmt)
pinkfoot_simdata = weight_data[weight_data['species']=='pinkfoot']
# silly trick: first encode the week
field_data['weekdate1']=field_data['Date'].dt.strftime('%Y-W%U')
# now decode it into the date, while installing the day of the week as sunday
field_data['weekdate2']=[dt.datetime.strptime(i+'-0', '%Y-W%U-%w') for i in field_data['weekdate1']]

field_agg=field_data.groupby('weekdate2').agg(weight_mean=('Weight', np.mean), weight_std=('Weight',np.std))



line10=ax10.errorbar(pinkfoot_simdata['daydate'],pinkfoot_simdata['mean_weight'],temp_data['mean_weight_sd'], capsize=3, ms=5, marker=".")
line11=ax10.errorbar(field_agg.index,field_agg['weight_mean'],field_agg['weight_std'], capsize=3, ms=5, marker=".")
ax10.legend(handles=[line10,line11], labels=['simulation', 'field data'], fancybox=True, shadow=True, title='Pinkfoot weights', loc='center right',bbox_to_anchor=(1.5, 0.60))



# Goose energetics
# Daily flight distance
energetics_data=pd.read_csv(data_dir+"GooseEnergeticsData.txt", sep='\t', header=0)
energetics_data['daydate']=my_dateparser(energetics_data['day'])
fig11, ax11 = plt.subplots()
months = mdates.MonthLocator()
myFmt = mdates.DateFormatter('%b')
# plt.sca()
fig11.autofmt_xdate(rotation='vertical')
ax11.xaxis.set_major_formatter(myFmt)
line12=[None]*3
line12_sh=[None]*3
for i in range(3):
    temp = energetics_data[energetics_data.species.eq(species_names[i]) & (energetics_data.flight_distance>0)]['flight_distance']/1000
    temp_sd = energetics_data[energetics_data.species.eq(species_names[i]) & (energetics_data.flight_distance>0)]['flight_distance_sd']/1000
    times = energetics_data[energetics_data.species.eq(species_names[i]) & (energetics_data.flight_distance>0)]['daydate']
    line12[i],=ax11.plot(times,temp, ms=5, marker=".")
    line12_sh[i]=ax11.fill_between(times, temp-temp_sd, temp+ temp_sd ,alpha=0.2,color=line12[i]._color)
ax11.legend(handles=line12, labels=species_names, fancybox=True, shadow=True, title='species', loc='center right',bbox_to_anchor=(1.5, 0.60))
fig11.suptitle('Daily flight distance')

# Foraging time
fig12, ax12 = plt.subplots()
months = mdates.MonthLocator()
myFmt = mdates.DateFormatter('%b')
fig12.autofmt_xdate(rotation='vertical')
ax12.xaxis.set_major_formatter(myFmt)
line13=[None]*3
line13_sh=[None]*3

for i in range(3):
    temp = energetics_data[energetics_data.species.eq(species_names[i]) & (energetics_data.flight_distance>0)]['foraging_time']
    temp_sd = energetics_data[energetics_data.species.eq(species_names[i]) & (energetics_data.flight_distance>0)]['foraging_time_sd']
    times = energetics_data[energetics_data.species.eq(species_names[i]) & (energetics_data.flight_distance>0)]['daydate']
    line13[i],=ax12.plot(times,temp, ms=5, marker=".")
    line13_sh[i]=ax12.fill_between(times, temp-temp_sd, temp+ temp_sd ,alpha=0.2,color=line12[i]._color)

ax12.plot(energetics_data.daydate,energetics_data.day_length, color='black')
ax12.annotate('day length', (mdates.date2num(dt.datetime(2010, 9, 1)), 700), xytext=(15, 15), textcoords='offset points')
ax12.legend(handles=line13, labels=species_names, fancybox=True, shadow=True, title='species', loc='center right',bbox_to_anchor=(1.5, 0.60))
ax12.set_ylabel('[min]')
fig12.suptitle('Daily foraging time')


# Daily energy balance
fig13, ax13 = plt.subplots()
months = mdates.MonthLocator()
myFmt = mdates.DateFormatter('%b')
fig13.autofmt_xdate(rotation='vertical')
ax13.xaxis.set_major_formatter(myFmt)
line14=[None]*3
line14_sh=[None]*3

for i in range(3):
    temp = energetics_data[(energetics_data.species.eq(species_names[i])) & (energetics_data.flight_distance>0)]['daily_energy_balance']
    temp_sd = energetics_data[(energetics_data.species.eq(species_names[i])) & (energetics_data.flight_distance>0)]['daily_energy_balance_sd']
    times = energetics_data[(energetics_data.species.eq(species_names[i])) & (energetics_data.flight_distance>0)]['daydate']
    line14[i],=ax13.plot(times,temp, ms=5, marker=".")
    line14_sh[i]=ax13.fill_between(times, temp-temp_sd, temp+ temp_sd ,alpha=0.2,color=line12[i]._color)

start = energetics_data.daydate.min()
end = energetics_data.daydate.max()
t = np.linspace(start.value, end.value, 100)
t = pd.to_datetime(t)
ax13.plot(t,np.zeros(len(t)), color='black')
ax13.legend(handles=line14, labels=species_names, fancybox=True, shadow=True, title='species', loc='center right',bbox_to_anchor=(1.5, 0.60))
ax13.set_ylabel('[kJ]')
fig13.suptitle('Daily energy balance ')

# Forage locations
locations_stats_data=pd.read_csv(data_dir+"GooseIndLocCountStats.txt", sep='\t', header=0)
locations_stats_data['daydate']=my_dateparser(locations_stats_data['day'])

fig14, ax14 = plt.subplots()
months = mdates.MonthLocator()
myFmt = mdates.DateFormatter('%b')
fig14.autofmt_xdate(rotation='vertical')
ax14.xaxis.set_major_formatter(myFmt)
line15=[None]*3
line15_sh=[None]*3

for i in range(3):
    temp = locations_stats_data[(locations_stats_data.species.eq(species_names[i])) & (locations_stats_data.n_forage_locs>0)]['n_forage_locs']
    temp_sd = locations_stats_data[(locations_stats_data.species.eq(species_names[i])) & (locations_stats_data.n_forage_locs>0)]['n_forage_locs_sd']
    times = locations_stats_data[(locations_stats_data.species.eq(species_names[i])) & (locations_stats_data.n_forage_locs>0)]['daydate']
    line15[i],=ax14.plot(times,temp, ms=5, marker=".")
    line15_sh[i]=ax14.fill_between(times, temp-temp_sd, temp+ temp_sd ,alpha=0.2,color=line12[i]._color)



ax14.legend(handles=line15, labels=species_names, fancybox=True, shadow=True, title='species', loc='center right',bbox_to_anchor=(1.5, 0.60))
ax14.set_ylabel('')
fig14.suptitle('Daily number of forage locations')

# Flocks stats
# we need forage data for this graph:
forage_data=pd.read_csv(data_dir+"GooseFieldForageData.txt", sep='\t', header=0, dtype={'day': np.int16}, converters={'last_sown_veg': str.strip, 'veg_type_chr': str.strip, 'previous_crop': str.strip})
# The field dayordinal has the current day counting from 1/1/0001
forage_data['dayordinal']=forage_data['day']+simulation_start_date_ordinal
# Useful function that parses the data 
#my_dateparser=(lambda x: pd.to_datetime(x,unit='D', origin=simulation_start_date))
# The field 'daydate includes the date of the day for the data'
forage_data['daydate']=my_dateparser(forage_data['day'])
forage_data['weekdate']=forage_data['daydate'].dt.strftime('%Y-W%U')
forage_data_months_filtered = forage_data[forage_data['geese'+is_timed_str]&((forage_data['daydate'].dt.month>7) | (forage_data['daydate'].dt.month<4))]
fig15, ax15 = plt.subplots(1,3,figsize=mpl.figure.figaspect(0.5)*2)
months = mdates.MonthLocator()
myFmt = mdates.DateFormatter('%b')
fig15.autofmt_xdate(rotation='vertical')

for i in range(3):
    ax15[i].xaxis.set_major_formatter(myFmt)
    ax15[i].xaxis.set_minor_locator(months)
    ax15[i].xaxis_date()
    ax15[i].grid()
    temp=forage_data_months_filtered[forage_data_months_filtered[species_names[i]+is_timed_str]>0].groupby('daydate')['season'].count()
    ax15[i].plot(temp.index, temp, ms=5, marker=".")
    ax15[i].set_title(species_names[i])
fig15.suptitle('Daily flocks number')
    
    
