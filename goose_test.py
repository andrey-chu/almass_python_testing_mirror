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
    ('CloverGrassGrazed2', 0, '*', '*')],
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
                    ('OFieldPeas', 0, '*', '*'),
     ]
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
print('Calculating new habitats--> Elapsed: %s' % (elapsed))
#rel_fields_ser = pd.Series(list(zip(forage_data['last_sown_veg'], 
#                                    forage_data['veg_phase'], forage_data['veg_type_chr'], forage_data['previous_crop'])))
#rel_fields_ser1 = pd.Series(list(zip(forage_data['last_sown_veg'], 
#                                    forage_data['veg_phase'])))
