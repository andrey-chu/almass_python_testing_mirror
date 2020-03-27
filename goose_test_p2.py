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

data_dir = "~/CLionProjects/GooseTests/run-directory1/"
source_dir = "~/CLionProjects/ALMaSS_all"
field_dir ="~/CLionProjects/GooseTests/ALMaSS_inputs"
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
    line9=ax9[i].errorbar(temp_data['daydate'],temp_data['mean_weight'],temp_data['mean_weight_se'], capsize=3, ms=5, marker=".")
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



line10=ax10.errorbar(pinkfoot_simdata['daydate'],pinkfoot_simdata['mean_weight'],temp_data['mean_weight_se'], capsize=3, ms=5, marker=".")
line11=ax10.errorbar(field_agg.index,field_agg['weight_mean'],field_agg['weight_std'], capsize=3, ms=5, marker=".")
ax10.legend(handles=[line10,line11], labels=['simulation', 'field data'], fancybox=True, shadow=True, title='Pinkfoot weights', loc='center right',bbox_to_anchor=(1.5, 0.60))



# Goose energetics
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
    temp = energetics_data[energetics_data.species.eq(species_names[i]) & energetics_data.flight_distance>0]['flight_distance']/1000
    temp_se = energetics_data[energetics_data.species.eq(species_names[i]) & energetics_data.flight_distance>0]['flight_distance_se']/1000
    times = energetics_data[energetics_data.species.eq(species_names[i]) & energetics_data.flight_distance>0]['daydate']
    line12[i],=ax11.plot(times,temp, ms=5, marker=".")
    line12_sh[i]=ax11.fill_between(times, temp-temp_se, temp+ temp_se ,alpha=0.2,color=line12[i]._color)
ax11.legend(handles=line12, labels=species_names, fancybox=True, shadow=True, title='species', loc='center right',bbox_to_anchor=(1.5, 0.60))
fig11.suptitle('Daily flight distance')