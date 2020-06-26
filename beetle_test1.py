#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 23 11:23:51 2020

@author: au517882
"""
import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib as mpl

simulation_start_date = dt.date(1991, 1, 1)# The year is probably incorrect: check for the right one
my_dateparser=(lambda x: pd.to_datetime(x,unit='D', origin=simulation_start_date))

stages_names=['Egg', 'Larva', 'Pupa', 'Adult']
stages_names.extend(['Unknown'])
results_dir1='~/CLionProjects/ALMaSS_debug/std_output/'
results_dir2='~/CLionProjects/ALMaSS_debug/mine_output/'
column_names=['Day']
column_names.extend(stages_names)
population_data1=pd.read_csv(results_dir1+"Probe.res", sep='\t', header=None, names=column_names)
population_data2=pd.read_csv(results_dir2+"Probe.res", sep='\t', header=None, names=column_names)
population_data1['Daydate']=my_dateparser(np.uint(population_data1['Day']))
population_data2['Daydate']=my_dateparser(np.uint(population_data2['Day']))

fig1, ax1 = plt.subplots(figsize=mpl.figure.figaspect(0.5)*2)
months = mdates.MonthLocator()
myFmt = mdates.DateFormatter('%b')
fig1.autofmt_xdate(rotation='vertical')
ax1.xaxis.set_major_formatter(myFmt)
ax1.xaxis.set_minor_locator(months)
ax1.xaxis_date()
ax1.grid()
time1 = population_data1['Daydate']
time2 = population_data2['Daydate']
line1=ax1.plot(time1, population_data1['Egg'], marker=None,  label='Std Egg')
line2=ax1.plot(time1, population_data1['Larva'], marker=None,  label='Std Larva')
line3=ax1.plot(time1, population_data1['Pupa'], marker=None,  label='Std Pupa')
line4=ax1.plot(time1, population_data1['Adult'], marker=None,  label='Std Adult')
line11=ax1.plot(time2, population_data2['Egg'], marker=".", color=line1[0]._color, label='Mine Egg')
line21=ax1.plot(time2, population_data2['Larva'], marker=".", color=line2[0]._color, label='Mine Larva')
line31=ax1.plot(time2, population_data2['Pupa'], marker=".", color=line3[0]._color, label='Mine Pupa')
line41=ax1.plot(time2, population_data2['Adult'], marker=".", color=line4[0]._color, label='Mine Adult')

ax1.legend( fancybox=True, shadow=True, title='Bembidion Stages', loc='center right',bbox_to_anchor=(1.1, 0.60))
ax1.set_title('Daily population size')
############################# Stages graph #######################################


stages_columnnames = ['Ignore', 'Year', 'TotalDay', 'DayInYear', 'YearNo', 'State', 'CanReproduce']
stages_data1=pd.read_csv(results_dir1+"debug.tsv", sep='\t', header=None, names=stages_columnnames, usecols=[2, 4, 5, 6], dtype={'TotalDay':'Int64', 'YearNo':'Int64', 'State':'Int64','CanReproduce':'Int64'}, skiprows=[0])
stages_data2=pd.read_csv(results_dir2+"debug.tsv", sep='\t', header=None, names=stages_columnnames, usecols=[2, 4, 5, 6], dtype={'TotalDay':'Int64', 'YearNo':'Int64', 'State':'Int64','CanReproduce':'Int64'}, skiprows=[0])
stages_data1_grouped=stages_data1.groupby(['TotalDay', 'State','CanReproduce']).size()
stages_data1_dead=stages_data1_grouped[stages_data1_grouped.index.get_level_values(1).isin([14])].reset_index().set_index('TotalDay').iloc[:,2]
stages_data1_dead.rename(lambda x: x -366)
stages_data1_dead_frame=stages_data1_dead.to_frame()
stages_data1_dead_frame['DayDate']=my_dateparser(np.uint(stages_data1_dead_frame.index))


stages_data2_grouped=stages_data2.groupby(['TotalDay', 'State','CanReproduce']).size()
stages_data2_dead=stages_data2_grouped[stages_data2_grouped.index.get_level_values(1).isin([14])].reset_index().set_index('TotalDay').iloc[:,2]
stages_data2_dead.rename(lambda x: x -366)
stages_data2_dead_frame=stages_data2_dead.to_frame()
stages_data2_dead_frame['DayDate']=my_dateparser(np.uint(stages_data2_dead_frame.index))

fig2, ax2 = plt.subplots(figsize=mpl.figure.figaspect(0.5)*2)
months = mdates.MonthLocator()
myFmt = mdates.DateFormatter('%b')
fig2.autofmt_xdate(rotation='vertical')
ax2.xaxis.set_major_formatter(myFmt)
ax2.xaxis.set_minor_locator(months)
ax2.xaxis_date()
ax2.grid()


line1=ax2.plot(stages_data1_dead_frame['DayDate'], stages_data1_dead_frame[0], marker=".",  label='orig')
line2=ax2.plot(stages_data2_dead_frame['DayDate'], stages_data2_dead_frame[0], marker=".",  label='mine')
ax2.legend( fancybox=True, shadow=True, title='Bembidion Daily death rate', loc='center right',bbox_to_anchor=(1.1, 0.60))
ax2.set_title('Bembidion model')