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
import pendulum
import zlib
import lzma
import zipfile
# this is definition whether we take into account timed values or not
# Is there a reason to use not timed values
is_timed = True

species_names = ["barnacle", "greylag", "pinkfoot"]
geese_foods = ['grain', 'grass', 'maize']
geese_foods_wcereal = ['grain', 'grass', 'maize', 'cereal']
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
source_dir = "ALMaSS_all" #"~/CLionProjects/ALMaSS_all"
# let us read the config data, it will be useful afterwards
CONFIG_PATH=data_dir+'TIALMaSSConfig.cfg'
with open(os.path.expanduser(CONFIG_PATH), 'r') as f:
    config_string = '[dummy_section]\n' + f.read()
config = configparser.ConfigParser(strict=False)
config.read_string(config_string)

simulation_start_date = dt.date(2009, 1, 1)# we should check again that this is a right date, probably should be read from somewhere
simulation_start_date_ordinal=dt.date.toordinal(simulation_start_date)

# Forage data first: unzip, (it was zipped by prepare in order to be uploadable) load data , while stripping the spaces 
#forage_data=pd.read_csv(data_dir+"GooseFieldForageData.txt", sep='\t', header=0, parse_dates=['day'], dtype={'day': 'str'},date_parser=my_dateparser)

with zipfile.ZipFile(data_dir+"GooseFieldForageData.txt.gz", 'r') as zip_ref:
    zip_ref.extractall(data_dir)
forage_data=pd.read_csv(data_dir+"GooseFieldForageData.txt", sep='\t', header=0, dtype={'day': np.int16}, converters={'last_sown_veg': str.strip, 'veg_type_chr': str.strip, 'previous_crop': str.strip})
# The field dayordinal has the current day counting from 1/1/0001
forage_data['dayordinal']=forage_data['day']+simulation_start_date_ordinal
# Useful function that parses the data 
my_dateparser=(lambda x: pd.to_datetime(x,unit='D', origin=simulation_start_date))
# The field 'daydate includes the date of the day for the data'
forage_data['daydate']=my_dateparser(forage_data['day'])
forage_data['weekdate']=forage_data['daydate'].dt.strftime('%Y-W%U')
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
# list of cereals this list comes from code: 
# bool Landscape::SupplyIsCereal2(TTypesOfVegetation a_vege_type) in Landscape.cpp
Cereals_list=[
	'SpringBarley',
	'SpringBarleySpr',
	'WinterBarley',
	'SpringWheat',
	'WinterWheat',
	'WinterRye',
	'Oats',
	'Triticale',
	'SpringBarleySeed',
	'SpringBarleyStrigling',
	'SpringBarleyStriglingSingle',
	'SpringBarleyStriglingCulm',
	'WinterWheatStrigling',
	'WinterWheatStriglingSingle',
	'WinterWheatStriglingCulm',
	'OWinterBarley',
	'OWinterBarleyExt',
	'OWinterRye',
	'SpringBarleyGrass',
	'SpringBarleyCloverGrass',
	'SpringBarleyPeaCloverGrassStrigling',
	'OSpringBarley',
	'OSpringBarleyPigs',
	'OWinterWheatUndersown',
	'OWinterWheat',
	'OOats',
	'OTriticale',
	'WWheatPControl',
	'WWheatPToxicControl',
	'WWheatPTreatment',
	'AgroChemIndustryCereal',
	'SpringBarleyPTreatment',
	'SpringBarleySKManagement',
	'OSpringBarleyExt',
	'OSpringBarleyGrass',
	'OSpringBarleyClover',
	'PLWinterWheat',
	'PLWinterBarley',
	'PLWinterRye',
	'PLWinterTriticale',
	'PLSpringWheat',
	'PLSpringBarley',
	'NLWinterWheat',
	'NLSpringBarley',
        ]
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


### Habitat use


###


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
    forage_data['max_intake_source_wcereal_'+i] =  forage_data['max_intake_source_'+i]
    # since when grass
    forage_data.loc[forage_data['veg_type_chr'].isin(Cereals_list) & (forage_data['max_intake_source_'+i]=='grass'),'max_intake_source_wcereal_'+i]='cereal'
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

forage_summary=forage_data_months_filtered.groupby(['weekdate', 'max_intake_source_barnacle', 
                                                    'max_intake_source_greylag', 'max_intake_source_pinkfoot']).agg(
                                                        barnacle_sum=('barnacle'+is_timed_str, sum),greylag_sum=(
                                                            'greylag'+is_timed_str, sum),pinkfoot_sum=(
                                                                'pinkfoot'+is_timed_str, sum))
forage_summary_wcereal=forage_data_months_filtered.groupby(['weekdate', 'max_intake_source_wcereal_barnacle', 
                                                    'max_intake_source_wcereal_greylag', 'max_intake_source_wcereal_pinkfoot']).agg(
                                                        barnacle_sum=('barnacle'+is_timed_str, sum),greylag_sum=(
                                                            'greylag'+is_timed_str, sum),pinkfoot_sum=(
                                                                'pinkfoot'+is_timed_str, sum))
fig4a, ax4a = plt.subplots(1,3,sharex='col', sharey='row', figsize=mpl.figure.figaspect(0.9)*2)
for j in range(3):
    
    
    months = mdates.MonthLocator()
    myFmt = mdates.DateFormatter('%b')
    # plt.sca()
    fig4a.autofmt_xdate(rotation='vertical')
    colours = ['blue', 'red', 'green', 'yellow']
    width = 5
    all_dates_str =  forage_summary_wcereal.index.get_level_values(0).unique()
    #all_dates=[pendulum.parse(i) for i in all_dates_str]
    all_dates=[dt.datetime.strptime(i+'-0', '%Y-W%U-%w') for i in all_dates_str]
    ax4a[j].xaxis.set_major_formatter(myFmt)
        
    ax4a[j].grid()
        
        
    ax4a[j].xaxis.set_minor_locator(months)
    ax4a[j].xaxis_date()
    grain_t=forage_summary_wcereal.xs('grain', level=1+j)[species_names[j]+'_sum'].reset_index(level=2, drop=True).reset_index(level=1, drop=True).groupby(level=0).agg(sum).reindex(all_dates_str).fillna(0)
    grass_t=forage_summary_wcereal.xs('grass', level=1+j)[species_names[j]+'_sum'].reset_index(level=2, drop=True).reset_index(level=1, drop=True).groupby(level=0).agg(sum).reindex(all_dates_str).fillna(0)
    maize_t=forage_summary_wcereal.xs('maize', level=1+j)[species_names[j]+'_sum'].reset_index(level=2, drop=True).reset_index(level=1, drop=True).groupby(level=0).agg(sum).reindex(all_dates_str).fillna(0)
    cereal_t=forage_summary_wcereal.xs('cereal', level=1+j)[species_names[j]+'_sum'].reset_index(level=2, drop=True).reset_index(level=1, drop=True).groupby(level=0).agg(sum).reindex(all_dates_str).fillna(0)
    p1=ax4a[j].bar(all_dates, grain_t, width, color=colours[0])
    p2=ax4a[j].bar(all_dates, grass_t, width, bottom=grain_t,color=colours[1])
    p3=ax4a[j].bar(all_dates, maize_t, width, bottom=grain_t+grass_t,color=colours[2])
    p4=ax4a[j].bar(all_dates, cereal_t, width, bottom=grain_t+grass_t+maize_t,color=colours[3])
    ax4a[j].set_title(species_names[j])
    
    ax4a[0].set_ylabel('Number of geese')
    ax4a[1].set_xlabel('Month')
ax4a[j].legend(handles=(p1[0],p2[0],p3[0], p4[0]),labels=geese_foods_wcereal, fancybox=True, shadow=True, title='Grazing on\n(food of maximum \nintake value\n in the location)', loc='center right',bbox_to_anchor=(2, 0.60), ncol=1)
fig4a, ax4a = plt.subplots(1,3,sharex='col', sharey='row', figsize=mpl.figure.figaspect(0.9)*2)
for j in range(3):
    
    
    months = mdates.MonthLocator()
    myFmt = mdates.DateFormatter('%b')
    # plt.sca()
    fig4a.autofmt_xdate(rotation='vertical')
    colours = ['blue', 'red', 'green', 'yellow']
    width = 5
    all_dates_str =  forage_summary_wcereal.index.get_level_values(0).unique()
    #all_dates=[pendulum.parse(i) for i in all_dates_str]
    all_dates=[dt.datetime.strptime(i+'-0', '%Y-W%U-%w') for i in all_dates_str]
    ax4a[j].xaxis.set_major_formatter(myFmt)
        
    ax4a[j].grid()
        
        
    ax4a[j].xaxis.set_minor_locator(months)
    ax4a[j].xaxis_date()
    grain_t=forage_summary_wcereal.xs('grain', level=1+j)[species_names[j]+'_sum'].reset_index(level=2, drop=True).reset_index(level=1, drop=True).groupby(level=0).agg(sum).reindex(all_dates_str).fillna(0)
    grass_t=forage_summary_wcereal.xs('grass', level=1+j)[species_names[j]+'_sum'].reset_index(level=2, drop=True).reset_index(level=1, drop=True).groupby(level=0).agg(sum).reindex(all_dates_str).fillna(0)
    maize_t=forage_summary_wcereal.xs('maize', level=1+j)[species_names[j]+'_sum'].reset_index(level=2, drop=True).reset_index(level=1, drop=True).groupby(level=0).agg(sum).reindex(all_dates_str).fillna(0)
    cereal_t=forage_summary_wcereal.xs('cereal', level=1+j)[species_names[j]+'_sum'].reset_index(level=2, drop=True).reset_index(level=1, drop=True).groupby(level=0).agg(sum).reindex(all_dates_str).fillna(0)
    sum_t=grain_t+cereal_t+grass_t+maize_t
    grain_t /=0.01*sum_t
    cereal_t/=0.01*sum_t
    maize_t/=0.01*sum_t
    grass_t/=0.01*sum_t
    p1=ax4a[j].bar(all_dates, grain_t.fillna(0), width, color=colours[0])
    p2=ax4a[j].bar(all_dates, grass_t.fillna(0), width, bottom=grain_t.fillna(0),color=colours[1])
    p3=ax4a[j].bar(all_dates, maize_t.fillna(0), width, bottom=grain_t.fillna(0)+grass_t.fillna(0),color=colours[2])
    p4=ax4a[j].bar(all_dates, cereal_t.fillna(0), width, bottom=grain_t.fillna(0)+grass_t.fillna(0)+maize_t.fillna(0),color=colours[3])
    ax4a[j].set_title(species_names[j])
    
    ax4a[0].set_ylabel('percent %')
    ax4a[2].set_xlabel('Month')   
ax4a[j].legend(handles=(p1[0],p2[0],p3[0], p4[0]),labels=geese_foods_wcereal, fancybox=True, shadow=True, title='Grazing on\n(food of maximum \nintake value\n in the location)', loc='center right',bbox_to_anchor=(2, 0.60), ncol=1)
#### field data
field_forage_data=pd.read_csv(data_dir+"habitat-use-2014.tsv", sep='\t', header=0)
field_forage_data.loc[field_forage_data['month']==1,'month']=13
ff_summary=field_forage_data.groupby(['month','species', 'habitat']).agg(sum)
xtick_locs = range(9, 14)
xtick_labs=['Sep', 'Oct', 'Nov', 'Dec', 'Jan']
fig4a, ax4a = plt.subplots(1,3,sharex='col', sharey='row', figsize=mpl.figure.figaspect(0.5)*2)
for j in range(3):
    
    
    months = mdates.MonthLocator()
    myFmt = mdates.DateFormatter('%b')
    # plt.sca()
    fig4a.autofmt_xdate(rotation='vertical')
    colours = ['blue', 'red', 'green', 'yellow', 'magenta']
    width = 0.9
    all_dates_str =  ff_summary.index.get_level_values(0).unique()

    #ax4a.xaxis.set_major_formatter(myFmt)
    #all_dates=[dt.datetime.strptime(i+, '%m') for i in all_dates_str]
    ax4a[j].grid()
    stubble_t=ff_summary.xs('Stubble', level=2).xs(species_names[j], level=1).reindex(all_dates_str).fillna(0)
    grass_t=ff_summary.xs('Grass', level=2).xs(species_names[j], level=1).reindex(all_dates_str).fillna(0)
    maize_t=ff_summary.xs('Maize', level=2).xs(species_names[j], level=1).reindex(all_dates_str).fillna(0)
    cereal_t=ff_summary.xs('WinterCereal', level=2).xs(species_names[j], level=1).reindex(all_dates_str).fillna(0)
    rape_t=ff_summary.xs('Rape', level=2).xs('pinkfoot', level=1).reindex(all_dates_str).fillna(0)
    p1=ax4a[j].bar(all_dates_str, stubble_t.N, width, color=colours[0], label='Stubble')
    p2=ax4a[j].bar(all_dates_str, grass_t.N, width, bottom=stubble_t.N,color=colours[1], label='Grass')
    p3=ax4a[j].bar(all_dates_str, maize_t.N, width, bottom=stubble_t.N+grass_t.N,color=colours[2], label='Maize')
    p4=ax4a[j].bar(all_dates_str, cereal_t.N, width, bottom=stubble_t.N+grass_t.N+maize_t.N,color=colours[3], label='Cereal')
    p5=ax4a[j].bar(all_dates_str, rape_t.N, width, bottom=stubble_t.N+grass_t.N+maize_t.N+cereal_t.N,color=colours[4], label='Rape')
    ax4a[j].set_xticks(xtick_locs)
    ax4a[j].set_xticklabels(xtick_labs)
    #ax4a[j].set_rotation(90)
    ax4a[j].set_title(species_names[j])
    
    ax4a[0].set_ylabel('Number of geese')
    ax4a[1].set_xlabel('Month')
ax4a[j].legend(fancybox=True, shadow=True, title='Habitat', loc='center right',bbox_to_anchor=(1.5, 0.60), ncol=1)


fig4a, ax4a = plt.subplots(1,3,sharex='col', sharey='row', figsize=mpl.figure.figaspect(0.5)*2)
for j in range(3):
    
    
    months = mdates.MonthLocator()
    myFmt = mdates.DateFormatter('%b')
    # plt.sca()
    fig4a.autofmt_xdate(rotation='vertical')
    colours = ['blue', 'red', 'green', 'yellow', 'magenta']
    width = 0.9
    all_dates_str =  ff_summary.index.get_level_values(0).unique()

    #ax4a.xaxis.set_major_formatter(myFmt)
    #all_dates=[dt.datetime.strptime(i+, '%m') for i in all_dates_str]
    ax4a[j].grid()
    stubble_t=ff_summary.xs('Stubble', level=2).xs(species_names[j], level=1).reindex(all_dates_str).fillna(0)
    grass_t=ff_summary.xs('Grass', level=2).xs(species_names[j], level=1).reindex(all_dates_str).fillna(0)
    maize_t=ff_summary.xs('Maize', level=2).xs(species_names[j], level=1).reindex(all_dates_str).fillna(0)
    cereal_t=ff_summary.xs('WinterCereal', level=2).xs(species_names[j], level=1).reindex(all_dates_str).fillna(0)
    rape_t=ff_summary.xs('Rape', level=2).xs('pinkfoot', level=1).reindex(all_dates_str).fillna(0)
    sum_t = stubble_t+grass_t+maize_t+cereal_t+rape_t
    stubble_t/=0.01*sum_t
    grass_t/=0.01*sum_t
    maize_t/=0.01*sum_t
    cereal_t/=0.01*sum_t
    rape_t/=0.01*sum_t
    p1=ax4a[j].bar(all_dates_str, stubble_t.N, width, color=colours[0], label='Stubble')
    p2=ax4a[j].bar(all_dates_str, grass_t.N, width, bottom=stubble_t.N,color=colours[1], label='Grass')
    p3=ax4a[j].bar(all_dates_str, maize_t.N, width, bottom=stubble_t.N+grass_t.N,color=colours[2], label='Maize')
    p4=ax4a[j].bar(all_dates_str, cereal_t.N, width, bottom=stubble_t.N+grass_t.N+maize_t.N,color=colours[3], label='Cereal')
    p5=ax4a[j].bar(all_dates_str, rape_t.N, width, bottom=stubble_t.N+grass_t.N+maize_t.N+cereal_t.N,color=colours[4], label='Rape')
    ax4a[j].set_xticks(xtick_locs)
    ax4a[j].set_xticklabels(xtick_labs)
    ax4a[j].set_title(species_names[j])
    
    ax4a[0].set_ylabel('percent %')
    ax4a[1].set_xlabel('Month')
ax4a[j].legend(fancybox=True, shadow=True, title='Habitat', loc='center right',bbox_to_anchor=(1.5, 0.60), ncol=1)  
#### Other sim data

sim_habdata=pd.read_csv(data_dir+"GooseHabitatUseStats.txt", sep='\t', header=0)
sim_habdata['daydate']=my_dateparser(sim_habdata['day'])
sim_habdata=sim_habdata[(sim_habdata['daydate'].dt.month>7) | (sim_habdata['daydate'].dt.month<5)]
sim_habdata_fieldsim=pd.read_csv(data_dir+"GooseHabitatUseFieldObsStats.txt", sep='\t', header=0)

sim_habdata_fieldsim['daydate']=my_dateparser(sim_habdata_fieldsim['day'])
sim_habdata_fieldsim=sim_habdata_fieldsim[((sim_habdata_fieldsim['daydate'].dt.month>7) | (sim_habdata_fieldsim['daydate'].dt.month<=5))&(sim_habdata_fieldsim['count']>0)]
sim_habdata_gr=sim_habdata.groupby(['daydate','species']).agg(sum)
sim_habdata_fieldsim_gr=sim_habdata_fieldsim.groupby(['daydate','species']).agg(sum)
fig4a, ax4a = plt.subplots(1,3,sharex='col', sharey='row', figsize=mpl.figure.figaspect(0.5)*2)
for j in range(3):
    
    
    months = mdates.MonthLocator()
    myFmt = mdates.DateFormatter('%b')
    # plt.sca()
    fig4a.autofmt_xdate(rotation='vertical')
    colours = ['blue', 'red', 'green', 'yellow', 'magenta']
    width = 15
    all_dates =  sim_habdata_fieldsim_gr.index.get_level_values(0).unique()

    ax4a[j].xaxis.set_major_formatter(myFmt)
    #all_dates=[dt.datetime.strptime(i+, '%m') for i in all_dates_str]
    ax4a[j].grid()
    grain_t=sim_habdata_fieldsim_gr.xs(species_names[j], level=1).reindex(all_dates).fillna(0)['grain']*100
    grass_t=sim_habdata_fieldsim_gr.xs(species_names[j], level=1).reindex(all_dates).fillna(0)['grass']*100
    maize_t=sim_habdata_fieldsim_gr.xs(species_names[j], level=1).reindex(all_dates).fillna(0)['maize']*100
    cereal_t=sim_habdata_fieldsim_gr.xs(species_names[j], level=1).reindex(all_dates).fillna(0)['winter_cereal']*100
    p1=ax4a[j].bar(all_dates, grain_t.fillna(0), width, color=colours[0], label='grain')
    p2=ax4a[j].bar(all_dates, grass_t.fillna(0), width, bottom=grain_t.fillna(0),color=colours[1], label='grass')
    p3=ax4a[j].bar(all_dates, maize_t.fillna(0), width, bottom=grain_t.fillna(0)+grass_t.fillna(0),color=colours[2], label='maize')
    p4=ax4a[j].bar(all_dates, cereal_t.fillna(0), width, bottom=grain_t.fillna(0)+grass_t.fillna(0)+maize_t.fillna(0),color=colours[3], label='cereal')
    ax4a[j].set_title(species_names[j])
    ax4a[0].set_ylabel('percent %')
    ax4a[1].set_xlabel('Month')
ax4a[j].legend(fancybox=True, shadow=True, title='Habitat', loc='center right',bbox_to_anchor=(1.5, 0.60), ncol=1)  
fig4a.suptitle('Habitats observations simulaton file (percentage)')
fig4a, ax4a = plt.subplots(1,3,sharex='col', sharey='row', figsize=mpl.figure.figaspect(0.5)*2)
for j in range(3):
    
    
    months = mdates.MonthLocator()
    myFmt = mdates.DateFormatter('%b')
    # plt.sca()
    fig4a.autofmt_xdate(rotation='vertical')
    colours = ['blue', 'red', 'green', 'yellow', 'magenta']
    width = 15
    all_dates =  sim_habdata_fieldsim_gr.index.get_level_values(0).unique()

    ax4a[j].xaxis.set_major_formatter(myFmt)
    #all_dates=[dt.datetime.strptime(i+, '%m') for i in all_dates_str]
    ax4a[j].grid()
    grain_t=sim_habdata_fieldsim_gr.xs(species_names[j], level=1).reindex(all_dates).fillna(0)['grain']*sim_habdata_fieldsim_gr.xs(species_names[j], level=1).reindex(all_dates).fillna(0)['count']
    grass_t=sim_habdata_fieldsim_gr.xs(species_names[j], level=1).reindex(all_dates).fillna(0)['grass']*sim_habdata_fieldsim_gr.xs(species_names[j], level=1).reindex(all_dates).fillna(0)['count']
    maize_t=sim_habdata_fieldsim_gr.xs(species_names[j], level=1).reindex(all_dates).fillna(0)['maize']*sim_habdata_fieldsim_gr.xs(species_names[j], level=1).reindex(all_dates).fillna(0)['count']
    cereal_t=sim_habdata_fieldsim_gr.xs(species_names[j], level=1).reindex(all_dates).fillna(0)['winter_cereal']*sim_habdata_fieldsim_gr.xs(species_names[j], level=1).reindex(all_dates).fillna(0)['count']
    p1=ax4a[j].bar(all_dates, grain_t.fillna(0), width, color=colours[0], label='grain')
    p2=ax4a[j].bar(all_dates, grass_t.fillna(0), width, bottom=grain_t.fillna(0),color=colours[1], label='grass')
    p3=ax4a[j].bar(all_dates, maize_t.fillna(0), width, bottom=grain_t.fillna(0)+grass_t.fillna(0),color=colours[2], label='maize')
    p4=ax4a[j].bar(all_dates, cereal_t.fillna(0), width, bottom=grain_t.fillna(0)+grass_t.fillna(0)+maize_t.fillna(0),color=colours[3], label='cereal')
    ax4a[j].set_title(species_names[j])
    ax4a[0].set_ylabel('number of individuals')
    ax4a[1].set_xlabel('Month')
ax4a[j].legend(fancybox=True, shadow=True, title='Habitat', loc='center right',bbox_to_anchor=(1.5, 0.60), ncol=1)  
fig4a.suptitle('Habitats observations simulaton file (total numbers)')
### Now the last thing is the elaborate estimation of habitat made by Lars:
forage_summary_Lars_hab=forage_data_months_filtered.groupby(['weekdate', 'habitat']).agg(
                                                        barnacle_sum=('barnacle'+is_timed_str, sum),greylag_sum=(
                                                            'greylag'+is_timed_str, sum),pinkfoot_sum=(
                                                                'pinkfoot'+is_timed_str, sum))
                                                                
                                                                
fig4a, ax4a = plt.subplots(1,3,sharex='col', sharey='row', figsize=mpl.figure.figaspect(0.5)*2)
for j in range(3):
    
    
    months = mdates.MonthLocator()
    myFmt = mdates.DateFormatter('%b')
    # plt.sca()
    fig4a.autofmt_xdate(rotation='vertical')
   
    width = 5
    all_dates_str =  forage_summary_Lars_hab.index.get_level_values(0).unique()
    all_habitats = forage_summary_Lars_hab.index.get_level_values(1).unique()
    all_dates=[dt.datetime.strptime(i+'-0', '%Y-W%U-%w') for i in all_dates_str]
    ax4a[j].xaxis.set_major_formatter(myFmt)
    #all_dates=[dt.datetime.strptime(i+, '%m') for i in all_dates_str]
    ax4a[j].grid()
    habitat_t = np.zeros([len(all_dates), len(all_habitats)])
    #bottoms = np.zeros([len(all_dates),1])
    for k in range(len(all_habitats)):
        habitat_t[:,k]=forage_summary_Lars_hab.xs(all_habitats[k], level=1).reindex(all_dates_str).fillna(0)[species_names[j]+'_sum']
        if k==0:
            ax4a[j].bar(list(all_dates), list(habitat_t[:,k]), width, label=all_habitats[k])
            bottoms = list(habitat_t[:,k])
        else:
            ax4a[j].bar(list(all_dates), list(habitat_t[:,k]), width,bottom=bottoms, label=all_habitats[k])
            bottoms=list(habitat_t[:,k]+np.array(bottoms))
    
    ax4a[j].set_title(species_names[j])
    ax4a[0].set_ylabel('number of individuals')
    ax4a[1].set_xlabel('Month')
ax4a[j].legend(fancybox=True, shadow=True, title='Habitat', loc='center right',bbox_to_anchor=(1.5, 0.60), ncol=1)  
fig4a.suptitle('Larse\'s habitats (total numbers)')
                          
#### Distance to the roost
for i in species_names:
    forage_data[i+'_wtd_roost_dist']=forage_data['roost_dist_'+i]*forage_data[i+is_timed_str]
#def wtavg_barnacle(x, sp_name):
def wtavg_roost(x, sp_name):
    try:
        #return np.sum(x['wtd_roost_dist_'])/ np.sum( x[sp_name+is_timed_str])
        return pd.Series([np.average(x['roost_dist_'+sp_name], weights = x[sp_name+is_timed_str])], index=['roost_'+sp_name])
    except ZeroDivisionError:
        return pd.Series([0], index=['roost_'+sp_name])
def wtavg_roost_field(x, sp_name):
    try:
        #return np.sum(x['wtd_roost_dist_'])/ np.sum( x[sp_name+is_timed_str])
        return pd.Series([np.average(x['dist'], weights = x['numbers'])], index=['roost_'+sp_name])
    except ZeroDivisionError:
        return pd.Series([0], index=['roost_'+sp_name])
def min_week(series):
    temp= np.min(series).week+1
    if temp == 53:
        return 0
    else:
        return temp
forage_summary_roost=pd.concat([forage_data_months_filtered.groupby(['weekdate']).apply(wtavg_roost,sp_name='barnacle'),
                               forage_data_months_filtered.groupby(['weekdate']).apply(wtavg_roost,sp_name='pinkfoot'),
                               forage_data_months_filtered.groupby(['weekdate']).apply(wtavg_roost,sp_name='greylag'), 
                               forage_data_months_filtered.groupby(['weekdate']).agg(week=('daydate', min_week))],
                               axis=1, join='outer')
roost_field_observ_data=pd.read_csv(data_dir+"fieldobs_01112017.tsv", sep='\t', header=0)
roost_field_observ_data['daydate']=[dt.datetime.strptime(i, '%Y-%m-%dT%H:%M:%SZ') for i in roost_field_observ_data.ObsDato]
barnacle_obs_roost=roost_field_observ_data[roost_field_observ_data.species=='Barnacle'].groupby(['species','week']).apply(wtavg_roost_field, sp_name='barnacle_obs').droplevel(0)
pinkfoot_obs_roost=roost_field_observ_data[roost_field_observ_data.species=='Pinkfoot'].groupby(['species','week']).apply(wtavg_roost_field, sp_name='pinkfoot_obs').droplevel(0)
#greylag_obs_roost=roost_field_observ_data[roost_field_observ_data.species=='Greylag'].groupby(['species','week']).apply(wtavg_roost_field, sp_name='greylag_obs').droplevel(0)
roost_data_comparable=pd.concat([forage_summary_roost.set_index('week'), pinkfoot_obs_roost, barnacle_obs_roost],axis=1, join='inner')
fig4a, ax4a = plt.subplots(1,2,sharex='col', sharey='row', figsize=mpl.figure.figaspect(0.5)*2)

months = mdates.MonthLocator()
myFmt = mdates.DateFormatter('%b')
# plt.sca()
fig4a.autofmt_xdate(rotation='vertical')
   

all_dates_str =  forage_summary_roost.index.get_level_values(0).unique()

all_dates=[dt.datetime.strptime(i+'-0', '%Y-W%U-%w') for i in all_dates_str]
ax4a[0].xaxis.set_major_formatter(myFmt)
#all_dates=[dt.datetime.strptime(i+, '%m') for i in all_dates_str]
ax4a[0].grid()

ax4a[0].plot(all_dates,forage_summary_roost.roost_barnacle, label='barnacle')
ax4a[0].plot(all_dates,forage_summary_roost.roost_pinkfoot, label='pinkfoot')
ax4a[0].plot(all_dates,forage_summary_roost.roost_greylag, label='greylag')
ax4a[0].legend(fancybox=True, shadow=True, title='Species',  ncol=1)
ax4a[0].set_title('Distance from the roost')
ax4a[0].set_xlabel('Month')
ax4a[0].set_ylabel('metres')
ax4a[1].grid()

p1,=ax4a[1].plot(roost_data_comparable.index,roost_data_comparable.roost_barnacle, label='barnacle sim', linestyle='-')
ax4a[1].plot(roost_data_comparable.index,roost_data_comparable.roost_barnacle_obs, label='barnacle field',linestyle='--', color=p1.get_color())
p1,=ax4a[1].plot(roost_data_comparable.index,roost_data_comparable.roost_pinkfoot, label='pinkfoot sim', linestyle='-')
ax4a[1].plot(roost_data_comparable.index,roost_data_comparable.roost_pinkfoot_obs, label='barnacle field',linestyle='--', color=p1.get_color())
#ax4a[1].plot(all_dates,forage_summary_roost.roost_pinkfoot, label='pinkfoot')
#ax4a[1].plot(all_dates,forage_summary_roost.roost_greylag, label='greylag')
ax4a[1].legend(fancybox=True, shadow=True, title='Species',  ncol=1)
ax4a[1].set_title('Distance from the roost vs field data')
ax4a[1].set_xlabel('Week')










#### vegetation heights graphs
barnacle_max = 13.4626
pinkfoot_max = 16.6134
greylag_max = 24.3769

veg_types = forage_data['veg_type_chr'].unique()
regexp = re.compile(".*[gG]rass.*") # everything that contains grass
grass_types = list(filter(regexp.match, veg_types))
# let us filter grasses: All grasses
forage_data_grass = forage_data[forage_data['veg_type_chr'].isin(grass_types)]
grass_1=forage_data_grass.groupby(['veg_type_chr', 'daydate']).agg(veg_mean=('veg_height', np.mean), veg_std=('veg_height',np.std))
grass_1['veg_up']=grass_1['veg_mean']+grass_1['veg_std']
grass_1['veg_down']=grass_1['veg_mean']-grass_1['veg_std']
# let us filter grasses: those that geese are foraging upon
veg_types1 = forage_data_months_filtered['veg_type_chr'].unique()

grass_types_foraged = list(filter(regexp.match, veg_types1))
forage_data_grass2 = forage_data_months_filtered[forage_data_months_filtered['veg_type_chr'].isin(grass_types_foraged)]
grass_2=forage_data_grass2.groupby(['veg_type_chr', 'daydate']).agg(veg_mean=('veg_height', np.mean), veg_std=('veg_height',np.std))
grass_2['veg_up']=grass_2['veg_mean']+grass_2['veg_std']
grass_2['veg_down']=grass_2['veg_mean']-grass_2['veg_std']



forage_data_grass3 = forage_data_months_filtered[forage_data_months_filtered['veg_type_chr'].isin(grass_types_foraged) &((forage_data_months_filtered['barnacle_timed']>0) & (forage_data_months_filtered['max_intake_source_barnacle'] == 'grass') | (forage_data_months_filtered['pinkfoot_timed']>0) & (forage_data_months_filtered['max_intake_source_pinkfoot'] == 'grass') | (forage_data_months_filtered['greylag_timed']>0) & (forage_data_months_filtered['max_intake_source_greylag'] == 'grass'))]
veg_types3 = forage_data_grass3['veg_type_chr'].unique()
grass_3=forage_data_grass3.groupby(['veg_type_chr', 'daydate']).agg(veg_mean=('veg_height', np.mean), veg_std=('veg_height',np.std))
grass_3['veg_up']=grass_3['veg_mean']+grass_3['veg_std']
grass_3['veg_down']=grass_3['veg_mean']-grass_3['veg_std']


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
ax5.annotate('Barnacle', (mdates.date2num(dt.datetime(2011, 3, 1)), barnacle_max), xytext=(-15, -15), textcoords='offset points', arrowprops=dict(arrowstyle='-|>'))
ax5.annotate('Pinkfoot', (mdates.date2num(dt.datetime(2011, 3, 1)), pinkfoot_max), xytext=(12, 12), textcoords='offset points', arrowprops=dict(arrowstyle='-|>'))
ax5.annotate('Greylag', (mdates.date2num(dt.datetime(2011, 3, 1)), greylag_max), xytext=(15, 15), textcoords='offset points', arrowprops=dict(arrowstyle='-|>'))
for i in range(len(grass_types)):
    
    p[i],=ax5.plot(grass_1.loc[(grass_types[i],)].index, grass_1.loc[(grass_types[i],)]['veg_mean'])
    p1[i]=ax5.fill_between(grass_1.loc[(grass_types[i],)].index, grass_1.loc[(grass_types[i],)]['veg_up'], grass_1.loc[(grass_types[i],)]['veg_down'],alpha=0.2,color=p[i]._color)
    #
fig5.suptitle('Grasses (all)')
ax5.legend(handles=p, labels=grass_types, fancybox=True, shadow=True, title='Vegetation types', loc='center right',bbox_to_anchor=(1.5, 0.60))

fig6, ax6 = plt.subplots()

months = mdates.MonthLocator()
myFmt = mdates.DateFormatter('%b')
# plt.sca()
fig6.autofmt_xdate(rotation='vertical')
ax6.xaxis.set_major_formatter(myFmt)

ax6.grid()
p1=[None]*len(grass_types_foraged)

ax6.xaxis.set_minor_locator(months)
ax6.xaxis_date()
p_foraged=[None]*len(grass_types_foraged)
p1_foraged=[None]*len(grass_types_foraged)
ax6.plot(grass_2.loc[(grass_types_foraged[1],)].index,barnacle_max*np.ones(len(grass_2.loc[(grass_types_foraged[1],)].index)), color='black')
ax6.plot(grass_2.loc[(grass_types_foraged[1],)].index,pinkfoot_max*np.ones(len(grass_2.loc[(grass_types_foraged[1],)].index)), color='black')
ax6.plot(grass_2.loc[(grass_types_foraged[1],)].index,greylag_max*np.ones(len(grass_2.loc[(grass_types_foraged[1],)].index)), color='black')
ax6.annotate('Barnacle', (mdates.date2num(dt.datetime(2011, 3, 1)), barnacle_max), xytext=(-15, -15), textcoords='offset points', arrowprops=dict(arrowstyle='-|>'))
ax6.annotate('Pinkfoot', (mdates.date2num(dt.datetime(2011, 3, 1)), pinkfoot_max), xytext=(12, 12), textcoords='offset points', arrowprops=dict(arrowstyle='-|>'))
ax6.annotate('Greylag', (mdates.date2num(dt.datetime(2011, 3, 1)), greylag_max), xytext=(15, 15), textcoords='offset points', arrowprops=dict(arrowstyle='-|>'))
for i in range(len(grass_types_foraged)):
    
    p_foraged[i],=ax6.plot(grass_2.loc[(grass_types_foraged[i],)].index, grass_2.loc[(grass_types_foraged[i],)]['veg_mean'])
    p1_foraged[i]=ax6.fill_between(grass_2.loc[(grass_types_foraged[i],)].index, grass_2.loc[(grass_types_foraged[i],)]['veg_up'], grass_2.loc[(grass_types_foraged[i],)]['veg_down'],alpha=0.2,color=p[i]._color)
    #
fig6.suptitle('Grasses (foraged)')
ax6.legend(handles=p_foraged, labels=grass_types_foraged, fancybox=True, shadow=True, title='Vegetation types', loc='center right',bbox_to_anchor=(1.5, 0.60))



fig6a, ax6a = plt.subplots()

months = mdates.MonthLocator()
myFmt = mdates.DateFormatter('%b')
# plt.sca()
fig6a.autofmt_xdate(rotation='vertical')
ax6a.xaxis.set_major_formatter(myFmt)

ax6a.grid()


ax6a.xaxis.set_minor_locator(months)
ax6a.xaxis_date()
p_foraged=[None]*len(veg_types3)
p1_foraged=[None]*len(veg_types3)
start = grass_3.index.get_level_values(1).min()
end = grass_3.index.get_level_values(1).max()
t = np.linspace(start.value, end.value, 100)
t = pd.to_datetime(t)

ax6a.plot(t,barnacle_max*np.ones(len(t)), color='black')
ax6a.plot(t,pinkfoot_max*np.ones(len(t)), color='black')
ax6a.plot(t,greylag_max*np.ones(len(t)), color='black')
ax6a.annotate('Barnacle', (mdates.date2num(dt.datetime(2011, 3, 1)), barnacle_max), xytext=(-15, -15), textcoords='offset points', arrowprops=dict(arrowstyle='-|>'))
ax6a.annotate('Pinkfoot', (mdates.date2num(dt.datetime(2011, 3, 1)), pinkfoot_max), xytext=(12, 12), textcoords='offset points', arrowprops=dict(arrowstyle='-|>'))
ax6a.annotate('Greylag', (mdates.date2num(dt.datetime(2011, 3, 1)), greylag_max), xytext=(15, 15), textcoords='offset points', arrowprops=dict(arrowstyle='-|>'))
for i in range(len(veg_types3)):
    
    p_foraged[i],=ax6a.plot(grass_3.loc[(veg_types3[i],)].index, grass_3.loc[(veg_types3[i],)]['veg_mean'])
    p1_foraged[i]=ax6a.fill_between(grass_3.loc[(veg_types3[i],)].index, grass_3.loc[(veg_types3[i],)]['veg_up'], grass_3.loc[(veg_types3[i],)]['veg_down'],alpha=0.2,color=p[i]._color)
    #
fig6a.suptitle('Grasses height (where it was foraged)')
ax6a.legend(handles=p_foraged, labels=list(veg_types3), fancybox=True, shadow=True, title='Vegetation types', loc='center right',bbox_to_anchor=(1.5, 0.60))



regexp = re.compile("^((?![gG]rass).)*$") # everything that does not contain grass
nongrass_types = list(filter(regexp.match, veg_types))
# let us filter grasses: All non-grasses
forage_data_nongrass = forage_data[forage_data['veg_type_chr'].isin(nongrass_types)]
nongrass_1=forage_data_nongrass.groupby(['veg_type_chr', 'daydate']).agg(veg_mean=('veg_height', np.mean), veg_std=('veg_height',np.std))
nongrass_1['veg_up']=nongrass_1['veg_mean']+nongrass_1['veg_std']
nongrass_1['veg_down']=nongrass_1['veg_mean']-nongrass_1['veg_std']
# let us filter non-grasses: those that geese are foraging upon

nongrass_types_foraged = list(filter(regexp.match, veg_types1))
forage_data_nongrass2 = forage_data_months_filtered[forage_data_months_filtered['veg_type_chr'].isin(nongrass_types_foraged)]
nongrass_2=forage_data_nongrass2.groupby(['veg_type_chr', 'daydate']).agg(veg_mean=('veg_height', np.mean), veg_std=('veg_height',np.std))
nongrass_2['veg_up']=nongrass_2['veg_mean']+nongrass_2['veg_std']
nongrass_2['veg_down']=nongrass_2['veg_mean']-nongrass_2['veg_std']




nongrass_types_foraged = list(filter(regexp.match, veg_types1))
forage_data_nongrass3 = forage_data_months_filtered[forage_data_months_filtered['veg_type_chr'].isin(nongrass_types_foraged) &((forage_data_months_filtered['barnacle_timed']>0) & (forage_data_months_filtered['max_intake_source_barnacle'] == 'grass') | (forage_data_months_filtered['pinkfoot_timed']>0) & (forage_data_months_filtered['max_intake_source_pinkfoot'] == 'grass') | (forage_data_months_filtered['greylag_timed']>0) & (forage_data_months_filtered['max_intake_source_greylag'] == 'grass'))]
veg_types3 = forage_data_nongrass3['veg_type_chr'].unique()
nongrass_3=forage_data_nongrass3.groupby(['veg_type_chr', 'daydate']).agg(veg_mean=('veg_height', np.mean), veg_std=('veg_height',np.std))
nongrass_3['veg_up']=nongrass_3['veg_mean']+nongrass_3['veg_std']
nongrass_3['veg_down']=nongrass_3['veg_mean']-nongrass_3['veg_std']

fig7, ax7 = plt.subplots()

months = mdates.MonthLocator()
myFmt = mdates.DateFormatter('%b')
# plt.sca()
fig7.autofmt_xdate(rotation='vertical')
ax7.xaxis.set_major_formatter(myFmt)
ax7.set_ylim(-10,50)
ax7.grid()
p1=[None]*len(nongrass_types)

ax7.xaxis.set_minor_locator(months)
ax7.xaxis_date()
p=[None]*len(nongrass_types)
ax7.plot(nongrass_1.loc[(nongrass_types[1],)].index,barnacle_max*np.ones(len(nongrass_1.loc[(nongrass_types[1],)].index)), color='black')
ax7.plot(nongrass_1.loc[(nongrass_types[1],)].index,pinkfoot_max*np.ones(len(nongrass_1.loc[(nongrass_types[1],)].index)), color='black')
ax7.plot(nongrass_1.loc[(nongrass_types[1],)].index,greylag_max*np.ones(len(nongrass_1.loc[(nongrass_types[1],)].index)), color='black')
ax7.annotate('Barnacle', (mdates.date2num(dt.datetime(2011, 3, 1)), barnacle_max), xytext=(-15, -15), textcoords='offset points', arrowprops=dict(arrowstyle='-|>'))
ax7.annotate('Pinkfoot', (mdates.date2num(dt.datetime(2011, 3, 1)), pinkfoot_max), xytext=(12, 12), textcoords='offset points', arrowprops=dict(arrowstyle='-|>'))
ax7.annotate('Greylag', (mdates.date2num(dt.datetime(2011, 3, 1)), greylag_max), xytext=(15, 15), textcoords='offset points', arrowprops=dict(arrowstyle='-|>'))
for i in range(len(nongrass_types)):
    
    p[i],=ax7.plot(nongrass_1.loc[(nongrass_types[i],)].index, nongrass_1.loc[(nongrass_types[i],)]['veg_mean'])
    p1[i]=ax7.fill_between(nongrass_1.loc[(nongrass_types[i],)].index, nongrass_1.loc[(nongrass_types[i],)]['veg_up'], nongrass_1.loc[(nongrass_types[i],)]['veg_down'],alpha=0.2,color=p[i]._color)
    #
fig7.suptitle('Non-grasses (all)')
ax7.legend(handles=p, labels=nongrass_types, fancybox=True, shadow=True, title='Vegetation types', loc='center right',bbox_to_anchor=(1.5, 0.60))

fig8, ax8 = plt.subplots()

months = mdates.MonthLocator()
myFmt = mdates.DateFormatter('%b')
# plt.sca()
fig8.autofmt_xdate(rotation='vertical')
ax8.xaxis.set_major_formatter(myFmt)

ax8.grid()

ax8.xaxis.set_minor_locator(months)
ax8.xaxis_date()
p_foraged=[None]*len(nongrass_types_foraged)
p1_foraged=[None]*len(nongrass_types_foraged)
start = nongrass_2.index.get_level_values(1).min()
end = nongrass_2.index.get_level_values(1).max()
t = np.linspace(start.value, end.value, 100)
t = pd.to_datetime(t)
ax8.plot(t,barnacle_max*np.ones(len(t)), color='black')
ax8.plot(t,pinkfoot_max*np.ones(len(t)), color='black')
ax8.plot(t,greylag_max*np.ones(len(t)), color='black')
ax8.annotate('Barnacle', (mdates.date2num(dt.datetime(2011, 3, 1)), barnacle_max), xytext=(-15, -15), textcoords='offset points', arrowprops=dict(arrowstyle='-|>'))
ax8.annotate('Pinkfoot', (mdates.date2num(dt.datetime(2011, 3, 1)), pinkfoot_max), xytext=(12, 12), textcoords='offset points', arrowprops=dict(arrowstyle='-|>'))
ax8.annotate('Greylag', (mdates.date2num(dt.datetime(2011, 3, 1)), greylag_max), xytext=(15, 15), textcoords='offset points', arrowprops=dict(arrowstyle='-|>'))
for i in range(len(nongrass_types_foraged)):
    
    p_foraged[i],=ax8.plot(nongrass_2.loc[(nongrass_types_foraged[i],)].index, nongrass_2.loc[(nongrass_types_foraged[i],)]['veg_mean'])
    p1_foraged[i]=ax8.fill_between(nongrass_2.loc[(nongrass_types_foraged[i],)].index, nongrass_2.loc[(nongrass_types_foraged[i],)]['veg_up'], nongrass_2.loc[(nongrass_types_foraged[i],)]['veg_down'],alpha=0.2,color=p[i]._color)
    #
fig8.suptitle('Non-grasses (foraged areas)')
ax8.legend(handles=p_foraged, labels=nongrass_types_foraged, fancybox=True, shadow=True, title='Vegetation types', loc='center right',bbox_to_anchor=(1.5, 0.60))


fig8a, ax8a = plt.subplots()

months = mdates.MonthLocator()
myFmt = mdates.DateFormatter('%b')
# plt.sca()
fig8a.autofmt_xdate(rotation='vertical')
ax8a.xaxis.set_major_formatter(myFmt)

ax8a.grid()

ax8a.xaxis.set_minor_locator(months)
ax8a.xaxis_date()
p_foraged=[None]*len(veg_types3)
p1_foraged=[None]*len(veg_types3)
start = nongrass_3.index.get_level_values(1).min()
end = nongrass_3.index.get_level_values(1).max()
t = np.linspace(start.value, end.value, 100)
t = pd.to_datetime(t)

ax8a.plot(t,barnacle_max*np.ones(len(t)), color='black')
ax8a.plot(t,pinkfoot_max*np.ones(len(t)), color='black')
ax8a.plot(t,greylag_max*np.ones(len(t)), color='black')
ax8a.annotate('Barnacle', (mdates.date2num(dt.datetime(2011, 3, 1)), barnacle_max), xytext=(-15, -15), textcoords='offset points', arrowprops=dict(arrowstyle='-|>'))
ax8a.annotate('Pinkfoot', (mdates.date2num(dt.datetime(2011, 3, 1)), pinkfoot_max), xytext=(12, 12), textcoords='offset points', arrowprops=dict(arrowstyle='-|>'))
ax8a.annotate('Greylag', (mdates.date2num(dt.datetime(2011, 3, 1)), greylag_max), xytext=(15, 15), textcoords='offset points', arrowprops=dict(arrowstyle='-|>'))
for i in range(len(veg_types3)):
    
    p_foraged[i],=ax8a.plot(nongrass_3.loc[(veg_types3[i],)].index, nongrass_3.loc[(veg_types3[i],)]['veg_mean'])
    p1_foraged[i]=ax8a.fill_between(nongrass_3.loc[(veg_types3[i],)].index, nongrass_3.loc[(veg_types3[i],)]['veg_up'], nongrass_3.loc[(veg_types3[i],)]['veg_down'],alpha=0.2,color=p[i]._color)
    #
fig8a.suptitle('Vegetation height (where non-grass was foraged by geese)')
ax8a.legend(handles=p_foraged, labels=list(veg_types3), fancybox=True, shadow=True, title='Vegetation types', loc='center right',bbox_to_anchor=(1.5, 0.60))



    
    