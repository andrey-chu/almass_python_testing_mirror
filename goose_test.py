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
import time
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import configparser, os
import re

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

data_dir = "~/CLionProjects/GooseTests/run-directory/"
source_dir = "~/CLionProjects/ALMaSS_all"
# let us read the config data, it will be useful afterwards
CONFIG_PATH=data_dir+'TIALMaSSConfig.cfg'
with open(os.path.expanduser(CONFIG_PATH), 'r') as f:
    config_string = '[dummy_section]\n' + f.read()
config = configparser.ConfigParser(strict=False)
config.read_string(config_string)

simulation_start_date = dt.date(2009, 1, 1)# we should check again that this is a right date, probably should be read from somewhere
simulation_start_date_ordinal=dt.date.toordinal(simulation_start_date)

# Forage data first: load data , while stripping the spaces 
#forage_data=pd.read_csv(data_dir+"GooseFieldForageData.txt", sep='\t', header=0, parse_dates=['day'], dtype={'day': 'str'},date_parser=my_dateparser)
forage_data=pd.read_csv(data_dir+"GooseFieldForageData.txt", sep='\t', header=0, dtype={'day': np.int16}, converters={'last_sown_veg': str.strip, 'veg_type_chr': str.strip, 'previous_crop': str.strip})
# The field dayordinal has the current day counting from 1/1/0001
forage_data['dayordinal']=forage_data['day']+simulation_start_date_ordinal
# Useful function that parses the data 
my_dateparser=(lambda x: pd.to_datetime(x,unit='D', origin=simulation_start_date))
# The field 'daydate includes the date of the day for the data'
forage_data['daydate']=my_dateparser(forage_data['day'])
forage_data['habitat'] = 'Unknown'
# A dictionary that will allow to map vegetation to habitat
# The value is a list of tuples of last_sown_veg, veg_phase, veg_type_chr, previous_crop
# Empty string means don't care
# The key is habitat (In current R file there different columns for each 
# species, but the resulting values are the same, so why?--> less code, less values is better)
veg_to_habitat_filt_keys=('last_sown_veg', 'veg_phase', 'veg_type_chr', 'previous_crop')

veg_to_habitat = {
    # Grasses: check that none is missing
    'Grass': [('PermanentGrassGrazed', [3,2,0], '*', '*'),
    ('PermanentGrassTussocky', [0,2], '*', '*'),
    ('CloverGrassGrazed1', [2,3], '*', '*'),
    ('CloverGrassGrazed2', 2, '*', '*'),
    ('OWinterWheatUndersown', 2, '*', '*'),
    ('OSeedGrass1', [3,2,0], '*', '*'),
    ('OSeedGrass2', [3,2,0], '*', '*'),
    ('SeedGrass2', [3,2,0], '*', '*'),
    ('SeedGrass1', [3,2,0], '*', '*'),
    ('OCloverGrassGrazed2', [0,2], '*', '*'),    
    ('OCloverGrassGrazed1', [0,2,3], '*', '*'), 
    ('CloverGrassGrazed1', 0, '*', '*'), 
    ('CloverGrassGrazed2', 0, '*', '*'),
    ('NaturalGrass', '*', '*', '*')],
    'Rape': [('WinterRape', [0,2,3], '*', '*')],
    'WinterCereal':[('SpringBarley', [0,1,2], '*', '*'),
                    ('WinterWheat', [0,1,2], '*', '*'),
                    ('OWinterWheat', [0,1,2], '*', '*'),
                    ('SprBarleyCloverGrass', [0,1,2], '*', '*'),
                    ('WinterRye', [0,1,2], '*','*'),
                    ('OBarleyPeaCloverGrass', [2,1,0], '*', '*'),
                    ('OWinterRye', [2,1,0], '*', '*'),
                    ('OSBarleySilage', [0,1,2], '*', '*'),
                    ('OCarrots', 1, '*', '*'),
                    ('OSpringBarley', [2,1,0], '*', '*'),
                    ('OTriticale', [0,1,2], '*', '*'),
                    ('WinterBarley', [0,1,2], '*', '*'),
                    ('Triticale', [0,1,2], '*', '*'),
                    ('SpringBarleySilage', [0,1,2], '*', '*'),
                    ('WinterRape', 1, '*', '*'),
                    ('OWinterWheatUndersown', [0,1], '*', '*'),
                    ('Undefined', 0, '*', '*'),
                    ('OOats', [0,1,2], '*', '*'),
                    ('Oats', [0,1,2], '*', '*'),
                    ('OFieldPeas', 0, '*', '*')],
    'Stubble': [(['WinterBarley', 'OBarleyPeaCloverGrass', 'SprBarleyCloverGrass', 
                  'SpringBarleySilage', 'OSBarleySilage', 'OWinterRye', 'WinterRye', 
                  'OSpringBarley', 'SpringBarley', 'WinterWheat', 'OWinterWheat', 'OOats', 
                  'Oats', 'OTriticale', 'OWinterWheatUndersown', 'Triticale', 'OFieldPeas'], 3, '*', '*'),
                (['CloverGrassGrazed1','SeedGrass1'], '*', '*', 'SprBarleyCloverGrass'),
                (['CloverGrassGrazed1','SeedGrass1'], '*', 'SprBarleyCloverGrass', '*'),
                ('CloverGrassGrazed1', '*', '*', 'SpringBarley')
        ],
    'Maize': [(['MaizeSilage','OMaizeSilage'], [0,1,2,3], '*', '*')
              ],
    'Undefined':[('Undefined', [2,3], '*', '*')]
    }

# let us combine the fields for testing
t = time.time()
for habitat_i in veg_to_habitat.keys():
    forage_data_idxx = [forage_data.mask(veg_to_habitat_filt_keys[0],t[0])
                        .mask(veg_to_habitat_filt_keys[1],t[1]).mask(veg_to_habitat_filt_keys[2],t[2])
                        .mask(veg_to_habitat_filt_keys[3],t[3]).index.values for t in veg_to_habitat[habitat_i]]
    idxs = np.concatenate(forage_data_idxx).ravel().tolist()

    forage_data.iloc[idxs, forage_data.columns.get_loc("habitat")] = habitat_i
elapsed = time.time() - t
print('Calculating new foraging habitats--> Elapsed: %s' % (elapsed))
# now let us filter the table where the geese exist and the months are between august and march
t = time.time()
forage_data_months_filtered = forage_data[forage_data['geese'+is_timed_str]&((forage_data['daydate'].dt.month>7) | (forage_data['daydate'].dt.month<4))]

species_habs_to_plot = {new_list: {new_list1:pd.DataFrame() for new_list1 in geese_foods} for new_list in species_names}
for i in range(len(species_names)):
    for j in range(len(geese_foods)):
        # temporary view that holds the areas/times when species are bigger than 0
        temp = forage_data_months_filtered[species_names[i]+is_timed_str]>0
        if geese_foods[j] == 'grass':
            species_habs_to_plot[species_names[i]][geese_foods[j]] = pd.DataFrame({'Date': forage_data_months_filtered[temp]['daydate'], 
                                                                                   'FlockSize': forage_data_months_filtered[temp][species_names[i]+is_timed_str],
                                                                                   ' kJ/min': forage_data_months_filtered[temp]['grass_'+species_names[i]]})
        else:
            if geese_foods[j] == 'grain':
                title1 = ' gr/m^2'
            else:
                title1 = ' kJ/m^2'
            
            species_habs_to_plot[species_names[i]][geese_foods[j]] = pd.DataFrame({'Date': forage_data_months_filtered[temp]['daydate'], 
                                                                                   'FlockSize': forage_data_months_filtered[temp][species_names[i]+is_timed_str],
                                                                                   title1: forage_data_months_filtered[temp][geese_foods[j]]})
elapsed = time.time() - t
print('Filtering foraging data--> Elapsed: %s' % (elapsed))
# There are many ways to visualise, we will try to use pandas/matplotlib visualisation first, when more needed we move to seaborn or altair
fig, ax = plt.subplots(3, 3, sharex='col', sharey='row', figsize=mpl.figure.figaspect(2.5)*2)

months = mdates.MonthLocator()
myFmt = mdates.DateFormatter('%b')
# plt.sca()
fig.autofmt_xdate(rotation='vertical')
# fig.suptitle('Available forage on the fields with geese')
for i in range(3):
    for j in range(3):
        ax[i,j].xaxis.set_major_formatter(myFmt)
        
        ax[i,j].grid()
        
        
        ax[i,j].xaxis.set_minor_locator(months)
        ax[i,j].xaxis_date()
        
        line1=ax[i,j].scatter(x=species_habs_to_plot[species_names[j]][geese_foods[i]].iloc[:,0], 
                    y=species_habs_to_plot[species_names[j]][geese_foods[i]].iloc[:,2], alpha=0.1, 
                    s=np.log10(species_habs_to_plot[species_names[j]][geese_foods[i]].iloc[:,1])*4)
        if j == 0:
            ax[i,j].set_ylabel(geese_foods[i]+': '+species_habs_to_plot[species_names[j]][geese_foods[i]].columns.values[2])
        if i == 0:
            ax[i,j].set_title(species_names[j])
        if i ==2 and j ==1:
            ax[i,j].legend(*line1.legend_elements("sizes", num=6), loc='upper center', bbox_to_anchor=(0.5, -0.15),fancybox=True, shadow=True, ncol=5, title='log(#birds)')
                


    

# We will add data for the feeding rate for maize and corn  into the table
# this does not include the amounts of the geese on the field: (goose density)
# C++ code (grain):
#       m_IntakeRateVSGrainDensity_PF = HollingsDiscCurveClass(cfg_H1A.value(), cfg_H1B.value(), cfg_H1C.value(), cfg_H1D.value(), cfg_H1E.value(), cfg_H1F.value());
# 		if (a_species == gs_Greylag) return m_IntakeRateVSGrainDensity_PF->GetY(a_graindensity) * 1.21;
#		else if (a_species == gs_Pinkfoot) return m_IntakeRateVSGrainDensity_PF->GetY(a_graindensity);
#		else return m_IntakeRateVSGrainDensity_PF->GetY(a_graindensity) * 0.74;
# // ---- Grain functional response calculated by Kevin on 13/10/2017 ---- //
#  /** \brief Attack rate in a type II functional response curve (Hollings disc equation) */
#  CfgFloat cfg_H1A("HOLLINGS_ONE_A", CFG_CUSTOM, 0.04217666);
#  /** \brief Handling time in a type II functional response curve (Hollings disc equation) */
#  CfgFloat cfg_H1B("HOLLINGS_ONE_B", CFG_CUSTOM, 0.0840075);
#  /** \brief Logical config to control if the curve should be reversed (i.e. 1 - value) */
#  CfgBool cfg_H1C("HOLLINGS_ONE_C", CFG_CUSTOM, false);
#  /** \brief Max x-value - at this point the curve tends to 0, must stop here to avoid negative values */
#  CfgFloat cfg_H1D("HOLLINGS_ONE_D", CFG_CUSTOM, 2500);
#  /** \brief Min x-value */
#  CfgFloat cfg_H1E("HOLLINGS_ONE_E", CFG_CUSTOM, 0);
#  /** \brief File name for functional response on grain for pinkfeet */
#  CfgStr cfg_H1F("HOLLINGS_ONE_G", CFG_CUSTOM, "KJIntakeAtDiffGrainDensities_PF");


# C++ code (maize):
#	m_IntakeRateVSMaizeDensity_BN = new HollingsDiscCurveClass( cfg_H2A.value(), cfg_H2B.value(), cfg_H2C.value(), cfg_H2D.value(), cfg_H2E.value(), cfg_H2F.value() );
#       		if (a_species == gs_Greylag) return m_IntakeRateVSMaizeDensity_BN->GetY(a_maizedensity) * 1.64;
#		else if (a_species == gs_Pinkfoot) return m_IntakeRateVSMaizeDensity_BN->GetY(a_maizedensity) * 1.35;
#		else return m_IntakeRateVSMaizeDensity_BN->GetY(a_maizedensity); 
#  // ---- Maize functional response Calculated by Kevin on 29/06/2018 ---- //
#  /** \brief Attack rate in a type II functional response curve (Hollings disc equation) */
#  CfgFloat cfg_H2A("HOLLINGS_TWO_A", CFG_CUSTOM, 0.04294186);
#  /** \brief Handling time in a type II functional response curve (Hollings disc equation) */
#  CfgFloat cfg_H2B("HOLLINGS_TWO_B", CFG_CUSTOM, 0.05844966);
#  /** \brief Logical config to control if the curve should be reversed (i.e. 1 - value) */
#  CfgBool cfg_H2C("HOLLINGS_TWO_C", CFG_CUSTOM, false);
#  /** \brief Max x-value - at this point the curve tends to 0, must stop here to avoid negative values */
#  CfgFloat cfg_H2D("HOLLINGS_TWO_D", CFG_CUSTOM, 2100);
#  /** \brief Min x-value */
#  CfgFloat cfg_H2E("HOLLINGS_TWO_E", CFG_CUSTOM, 0);
#  /** \brief File name for functional response maize for barnacle */
#  CfgStr cfg_H2F("HOLLINGS_TWO_G", CFG_CUSTOM, "KJIntakeAtDiffMaizeDensities_BN");     
# HollingsDiscCurveClass::HollingsDiscCurveClass(double a_A, double a_B, bool a_reversecurve,
# 										       double a_MaxX, double a_MinX, const char* a_name)
# 	: CurveClass( a_reversecurve, a_MaxX, a_MinX, a_name ) {
# 	m_parameterA = a_A;
# 	m_parameterB = a_B;
# 	CalculateCurveValues();
# }
# double HollingsDiscCurveClass::DoCalc( double a_x ) {
# 	return ((a_x * m_parameterA) / (1 + m_parameterA * m_parameterB * a_x));
# }
# double CurveClass::GetY(double a_X)
# {
# 	/** This is the time sensitive method so we avoid division, rather use multiplication by the inverse of m_step. 
# 	Here we have a choice if a_X is bigger than maxX - either return the value for maxX or return parameter A (asymptote) */
# 	if (a_X > m_parameterMaxX) return m_values[9999]; //return m_parameterA;
# 	/** If a_X is <= minX then we need to return minX */
# 	if (a_X <= m_parameterMinX) return m_values[0];
# 	/** Otherwise we have to calculate which index is closest to a_X */
# 	int index = (int)((a_X - m_parameterMinX)* m_step_inv);
# 	/** Find and return the correct Y-value */
# 	return m_values[index];
# }
            
            
# default values for HollingDiskCurve for grain and maize (taken from source code)
param_A_grain = 0.04217666
param_B_grain = 0.0840075
param_A_maize = 0.04294186
param_B_maize = 0.05844966
# scaling parameters between the species (taken from source code)
grain_PF_to_GL = 1.21
grain_PF_to_BL = 0.74

maize_BL_to_GL = 1.64
maize_BL_to_PF = 1.35



# let us check whether defaults are not overridden in config file

param_A_grain=config.get('dummy_section', 'hollings_one_a (float)', fallback=param_A_grain)
param_B_grain=config.get('dummy_section', 'hollings_one_b (float)', fallback=param_B_grain)

param_A_maize=config.get('dummy_section', 'hollings_two_a (float)', fallback=param_A_maize)
param_B_maize=config.get('dummy_section', 'hollings_two_b (float)', fallback=param_B_maize)

## Let us try grain
grain_availability=np.arange(start = 0, stop = 2000)

grain_intake_PF = (grain_availability * param_A_grain)/(1+param_A_grain*param_B_grain*grain_availability)
grain_intake_GL=grain_intake_PF* grain_PF_to_GL
grain_intake_BL=grain_intake_PF* grain_PF_to_BL
fig1, ax1 = plt.subplots()
p1,=ax1.plot(grain_availability, grain_intake_PF)
p2,=ax1.plot(grain_availability, grain_intake_GL)
p3,=ax1.plot(grain_availability, grain_intake_BL)
ax1.grid()

fig1.legend([p1,p2,p3],['pinkfoot', 'greylag', 'barnacle'])
fig1.suptitle('Grain')
fig1.show()

## Let us try maize
maize_availability=np.arange(start = 0, stop = 2100)

maize_intake_BL = (maize_availability * param_A_maize)/(1+param_A_maize*param_B_maize*maize_availability)
maize_intake_GL=maize_intake_BL*  maize_BL_to_GL
maize_intake_PF=maize_intake_BL* maize_BL_to_PF
fig2, ax2 = plt.subplots()
p1,=ax2.plot(maize_availability, maize_intake_PF)
p2,=ax2.plot(maize_availability, maize_intake_GL)
p3,=ax2.plot(maize_availability, maize_intake_BL)
ax2.grid()

fig2.legend([p1,p2,p3],['pinkfoot', 'greylag', 'barnacle'])
fig2.suptitle('Maize')
fig2.show()

# All seems fine, let us estimate the feeding rate
maize_intake_params={'paramA':param_A_maize, 'paramB':param_B_maize, 'BL_to_GL':maize_BL_to_GL, 'BL_to_PF':maize_BL_to_PF}
grain_intake_params={'paramA':param_A_grain, 'paramB':param_B_grain, 'PF_to_GL':grain_PF_to_GL, 'PF_to_BL':grain_PF_to_BL}
def calc_maize_intake(x, maize_intake_params, species_inp):
    if species_inp == 'barnacle':
        return (x * maize_intake_params['paramA'])/(1+maize_intake_params['paramA']*maize_intake_params['paramB']*x)
    elif species_inp == 'greylag':
        return (x * maize_intake_params['paramA'])/(1+maize_intake_params['paramA']*maize_intake_params['paramB']*x)*maize_intake_params['BL_to_GL']
    elif species_inp == 'pinkfoot':
        return (x * maize_intake_params['paramA'])/(1+maize_intake_params['paramA']*maize_intake_params['paramB']*x)*maize_intake_params['BL_to_PF']
def calc_grain_intake(x, grain_intake_params, species_inp):
    if species_inp == 'pinkfoot':
        return (x * grain_intake_params['paramA'])/(1+grain_intake_params['paramA']*grain_intake_params['paramB']*x)
    elif species_inp == 'barnacle':
        return (x * grain_intake_params['paramA'])/(1+grain_intake_params['paramA']*grain_intake_params['paramB']*x)*grain_intake_params['PF_to_BL']
    elif species_inp == 'greylag':
        return (x * grain_intake_params['paramA'])/(1+grain_intake_params['paramA']*grain_intake_params['paramB']*x)*grain_intake_params['PF_to_GL']

forage_data['maize_intake_barnacle'] = calc_maize_intake(forage_data['maize'], maize_intake_params, 'barnacle')
forage_data['maize_intake_pinkfoot'] = calc_maize_intake(forage_data['maize'], maize_intake_params, 'pinkfoot')
forage_data['maize_intake_greylag'] = calc_maize_intake(forage_data['maize'], maize_intake_params, 'greylag')



forage_data['grain_intake_barnacle'] = calc_grain_intake(forage_data['grain'], grain_intake_params, 'barnacle')
forage_data['grain_intake_pinkfoot'] = calc_grain_intake(forage_data['grain'], grain_intake_params, 'pinkfoot')
forage_data['grain_intake_greylag'] = calc_grain_intake(forage_data['grain'], grain_intake_params, 'greylag')

for i in species_names:
    forage_data['max_intake_'+i] = forage_data[['grain_intake_'+i,'grass_'+i,'maize_intake_'+i]].max(axis=1)
    ttemp = pd.DataFrame(data=forage_data[['grain_intake_'+i,'grass_'+i,'maize_intake_'+i]])
    ttemp.columns = geese_foods
    forage_data['max_intake_source_'+i] = ttemp.idxmax(axis=1)
del ttemp
forage_data_months_filtered = forage_data[forage_data['geese'+is_timed_str]&((forage_data['daydate'].dt.month>7) | (forage_data['daydate'].dt.month<4))]

# Now let's do the same graph, but plotting only if the specific food has maximum intake rate on the specific field
# Meaning it is being eaten (most of the cases, if the logic is correct)

t = time.time()

species_foods_to_plot = {new_list: {new_list1:pd.DataFrame() for new_list1 in geese_foods} for new_list in species_names}
for i in range(len(species_names)):
    for j in range(len(geese_foods)):
        # temporary view that holds the areas/times when species are bigger than 0
        temp = (forage_data_months_filtered[species_names[i]+is_timed_str]>0) & (forage_data_months_filtered['max_intake_source_'+species_names[i]]==geese_foods[j])
 
        species_foods_to_plot[species_names[i]][geese_foods[j]] = pd.DataFrame({'Date': forage_data_months_filtered[temp]['daydate'], 
                                                                                   'FlockSize': forage_data_months_filtered[temp][species_names[i]+is_timed_str],
                                                                                   ' kJ/min': forage_data_months_filtered[temp]['max_intake_'+species_names[i]]})
 
elapsed = time.time() - t
print('Filtering foraging data--> Elapsed: %s' % (elapsed))


fig3, ax3 = plt.subplots(3, 3, sharex='col', sharey='row', figsize=mpl.figure.figaspect(2.5)*2)

months = mdates.MonthLocator()
myFmt = mdates.DateFormatter('%b')
# plt.sca()
fig3.autofmt_xdate(rotation='vertical')
# fig.suptitle('Available forage on the fields with geese')
for i in range(3):
    for j in range(3):
        ax3[i,j].xaxis.set_major_formatter(myFmt)
        
        ax3[i,j].grid()
        
        
        ax3[i,j].xaxis.set_minor_locator(months)
        ax3[i,j].xaxis_date()
        
        line1=ax3[i,j].scatter(x=species_foods_to_plot[species_names[j]][geese_foods[i]].iloc[:,0], 
                    y=species_foods_to_plot[species_names[j]][geese_foods[i]].iloc[:,2], alpha=0.1, 
                    s=np.log10(species_foods_to_plot[species_names[j]][geese_foods[i]].iloc[:,1])*8, color='blue')
        if j == 0:
            ax3[i,j].set_ylabel(geese_foods[i]+': '+species_foods_to_plot[species_names[j]][geese_foods[i]].columns.values[2])
        if i == 0:
            ax3[i,j].set_title(species_names[j])
        if i ==2 and j ==1:
            marker1 = ax3[i,j].scatter([],[], s=np.log10(10)*8, color='blue',alpha=0.1)
            marker2 = ax3[i,j].scatter([],[], s=np.log10(100)*8, color='blue',alpha=0.1)
            marker3 = ax3[i,j].scatter([],[], s=np.log10(1000)*8, color='blue',alpha=0.1)
            legend_markers = [marker1, marker2, marker3]

            labels1 = ["log(num)=log(10)","log(num)=log(100)","log(num)=log(1000)"]
            #ax[i,j].legend(*line1.legend_elements("sizes", num=6), loc='upper center', bbox_to_anchor=(0.5, -0.15),fancybox=True, shadow=True, ncol=5, title='log(#birds)')
            ax3[i,j].legend(handles=legend_markers, labels=labels1, loc='upper center', scatterpoints=1,bbox_to_anchor=(0.5, -0.15),fancybox=True, shadow=True, ncol=5, title='log(#birds)')

fig4, ax4 = plt.subplots(1, 3, sharex='col', sharey='row', figsize=mpl.figure.figaspect(1.5)*2)

months = mdates.MonthLocator()
myFmt = mdates.DateFormatter('%b')
# plt.sca()
fig4.autofmt_xdate(rotation='vertical')
colours = ['blue', 'red', 'green']
for i in range(3):
    for j in range(3):
        ax4[j].xaxis.set_major_formatter(myFmt)
        
        ax4[j].grid()
        
        
        ax4[j].xaxis.set_minor_locator(months)
        ax4[j].xaxis_date()
        
        line1=ax4[j].scatter(x=species_foods_to_plot[species_names[j]][geese_foods[i]].iloc[:,0], 
                    y=species_foods_to_plot[species_names[j]][geese_foods[i]].iloc[:,2], alpha=0.1, 
                    s=np.log10(species_foods_to_plot[species_names[j]][geese_foods[i]].iloc[:,1])*8, color=colours[i])
        if j == 0:
            ax4[j].set_ylabel(species_foods_to_plot[species_names[j]][geese_foods[i]].columns.values[2])
        if i == 0:
            ax4[j].set_title(species_names[j])
        if j ==1:
            marker1 = ax4[j].scatter([],[], s=np.log10(10)*8, color='blue',alpha=0.1)
            marker2 = ax4[j].scatter([],[], s=np.log10(100)*8, color='red',alpha=0.1)
            marker3 = ax4[j].scatter([],[], s=np.log10(1000)*8, color='green',alpha=0.1)
            legend_markers = [marker1, marker2, marker3]

            labels1 = ["10 geese on grain","100 geese on grass","1000 geese on maize"]
            #ax[i,j].legend(*line1.legend_elements("sizes", num=6), loc='upper center', bbox_to_anchor=(0.5, -0.15),fancybox=True, shadow=True, ncol=5, title='log(#birds)')
            ax4[j].legend(handles=legend_markers, labels=labels1, loc='upper center', scatterpoints=1,bbox_to_anchor=(0.5, -0.15),fancybox=True, shadow=True, ncol=5, title='log(#birds)')


#### vegetation heights graphs
barnacle_max = 13.4626
pinkfoot_max = 16.6134
greylag_max = 24.3769

veg_types = forage_data['veg_type_chr'].unique()
regexp = re.compile(".*[gG]rass.*") # everything that contains grass
grass_types = list(filter(regexp.match, veg_types))
# let us filter grasses
forage_data_grass = forage_data[forage_data['veg_type_chr'].isin(grass_types)]
grass_1=forage_data_grass.groupby(['veg_type_chr', 'daydate']).agg(veg_mean=('veg_height', np.mean), veg_std=('veg_height',np.std))
grass_1['veg_up']=grass_1['veg_mean']+grass_1['veg_std']
grass_1['veg_down']=grass_1['veg_mean']-grass_1['veg_std']

fig5, ax5 = plt.subplots()

months = mdates.MonthLocator()
myFmt = mdates.DateFormatter('%b')
# plt.sca()
fig5.autofmt_xdate(rotation='vertical')
ax5.xaxis.set_major_formatter(myFmt)

ax5.grid()
p1=[None]*len(grass_types)

ax5.xaxis.set_minor_locator(months)
ax5.xaxis_date()
p=[None]*len(grass_types)
ax5.plot(grass_1.loc[(grass_types[1],)].index,barnacle_max*np.ones(len(grass_1.loc[(grass_types[1],)].index)), color='black')
ax5.plot(grass_1.loc[(grass_types[1],)].index,pinkfoot_max*np.ones(len(grass_1.loc[(grass_types[1],)].index)), color='black')
ax5.plot(grass_1.loc[(grass_types[1],)].index,greylag_max*np.ones(len(grass_1.loc[(grass_types[1],)].index)), color='black')
for i in range(len(grass_types)):
    
    p[i],=ax5.plot(grass_1.loc[(grass_types[i],)].index, grass_1.loc[(grass_types[i],)]['veg_mean'])
    p1[i]=ax5.fill_between(grass_1.loc[(grass_types[i],)].index, grass_1.loc[(grass_types[i],)]['veg_up'], grass_1.loc[(grass_types[i],)]['veg_down'],alpha=0.2,color=p[i]._color)
    #
fig5.suptitle('Grasses')
ax5.legend(handles=p, labels=grass_types, fancybox=True, shadow=True, title='Vegetation types', loc='center right',bbox_to_anchor=(1.5, 0.60))