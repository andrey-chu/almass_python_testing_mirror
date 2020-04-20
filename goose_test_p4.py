#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  3 14:41:57 2020

@author: andrey
"""
import pandas as pd
import datetime as dt
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.dates as mdates
import configparser, os, glob
import re
import zlib
import lzma
import zipfile

simulation_start_date = dt.date(2009, 1, 1)# we should check again that this is a right date, probably should be read from somewhere
simulation_start_date_ordinal=dt.date.toordinal(simulation_start_date)
my_dateparser=(lambda x: pd.to_datetime(x,unit='D', origin=simulation_start_date))

is_timed = True

species_names = ["barnacle", "greylag", "pinkfoot"]
geese_foods = ['grain', 'grass', 'maize']
if is_timed==True:
    is_timed_str = '_timed'
else:
    is_timed_str = ''


data_dir = "rundir/"#"~/CLionProjects/GooseTests/run-directory1/"
#source_dir = "source"#"~/CLionProjects/ALMaSS_all"
field_dir ="fielddir"#"~/CLionProjects/GooseTests/ALMaSS_inputs"
# let us read the config data, it will be useful afterwards
CONFIG_PATH=data_dir+'TIALMaSSConfig.cfg'
with open(os.path.expanduser(CONFIG_PATH), 'r') as f:
    config_string = '[dummy_section]\n' + f.read()
config = configparser.ConfigParser(strict=False)
config.read_string(config_string)

### Geese numbers
population_data=pd.read_csv(data_dir+"GoosePopulationData.txt", sep='\t', header=0)
population_data['daydate']=my_dateparser(np.uint(population_data['day']))
fig1, ax1 = plt.subplots(figsize=mpl.figure.figaspect(0.5)*2)
months = mdates.MonthLocator()
myFmt = mdates.DateFormatter('%b')
fig1.autofmt_xdate(rotation='vertical')
ax1.xaxis.set_major_formatter(myFmt)
ax1.xaxis.set_minor_locator(months)
ax1.xaxis_date()
ax1.grid()
time = population_data['daydate']
line1=ax1.plot(time, population_data['pf_families'], marker="o", color='r', label='Pinkfoot families')
line2=ax1.plot(time, population_data['pf_non_breeders'], marker=".", color='r', label='Pinkfoot non-breeders')
line3=ax1.plot(time, population_data['gl_families'], marker="o", color='k', label='Greylag families')
line4=ax1.plot(time, population_data['gl_non_breeders'], marker=".", color='k', label='Greylag non-breeders')
line5=ax1.plot(time, population_data['bn_families'], marker="o", color='b', label='Barnackle families')
line6=ax1.plot(time, population_data['bn_non_breeders'], marker=".", color='b', label='Barnackle non-breeders')
ax1.legend( fancybox=True, shadow=True, title='species', loc='center right',bbox_to_anchor=(1.1, 0.60))
ax1.set_title('Daily population size')

### Leave reason
leave_data=pd.read_csv(data_dir+"GooseLeaveReasonStats.txt", sep='\t', header=0)
leave_data['daydate']=my_dateparser(np.uint(leave_data['day']))

fig2, ax2 = plt.subplots(1,3,figsize=mpl.figure.figaspect(0.5)*2)
months = mdates.MonthLocator()
myFmt = mdates.DateFormatter('%b')
fig2.autofmt_xdate(rotation='vertical')
colours = ['blue', 'red', 'green', 'yellow']
for i in range(3):
    ax2[i].xaxis.set_major_formatter(myFmt)
    ax2[i].xaxis.set_minor_locator(months)
    ax2[i].xaxis_date()
    ax2[i].grid()
    temp=leave_data[leave_data.species_type==species_names[i]+'_nonbreeder'].groupby(['daydate', 'leave_reason']).agg(num_left=('n', 'sum'))
    for j in range(len(temp.index.unique(1))):
        ax2[i].plot(temp.xs(temp.index.unique(1)[j],level=1).index, temp.xs(temp.index.unique(1)[j],level=1), ms=5, marker=".", color=colours[j],label=temp.index.unique(1)[j])
    ax2[i].set_title(species_names[i])
    ax2[i].legend(fancybox=True, shadow=True,loc='upper center',bbox_to_anchor=(0.5, 1.0), ncol=1)
    
fig2.suptitle('Daily number emmigrated')

# Flock sizes
with zipfile.ZipFile(data_dir+"GooseFieldForageData.txt.gz", 'r') as zip_ref:
    zip_ref.extractall(data_dir)
forage_data=pd.read_csv(data_dir+"GooseFieldForageData.txt", sep='\t', header=0, dtype={'day': np.int16}, converters={'last_sown_veg': str.strip, 'veg_type_chr': str.strip, 'previous_crop': str.strip})
field_data = pd.read_csv(data_dir+"fieldobs_01112017.tsv", sep='\t', header=0, converters={'species':str.lower})
# The field dayordinal has the current day counting from 1/1/0001
forage_data['dayordinal']=forage_data['day']+simulation_start_date_ordinal
# Useful function that parses the data 
#my_dateparser=(lambda x: pd.to_datetime(x,unit='D', origin=simulation_start_date))
# The field 'daydate includes the date of the day for the data'
forage_data['daydate']=my_dateparser(forage_data['day'])
forage_data['weekdate']=forage_data['daydate'].dt.strftime('%Y-W%U')
forage_data_months_filtered = forage_data[forage_data['geese'+is_timed_str]&((forage_data['daydate'].dt.month>7) | (forage_data['daydate'].dt.month<4))]
fig3, ax3 = plt.subplots(1,3,figsize=mpl.figure.figaspect(0.5)*2)
for i in range(3):
    temp=forage_data_months_filtered[forage_data_months_filtered[species_names[i]+is_timed_str]>0][species_names[i]+is_timed_str]
    if species_names[i] != 'greylag':
        temp1 = field_data[field_data['species']==species_names[i]].numbers
        ax3[i].hist(temp1, label='field data', bins=30, alpha=0.5, density='True')
    ax3[i].hist(temp, label='simulation', bins=30, alpha=0.5, density='True')
    
    ax3[i].legend(fancybox=True, shadow=True,loc='upper center',bbox_to_anchor=(0.5, 1.0), ncol=1)
    ax3[i].set_title(species_names[i])