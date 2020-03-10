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

data_dir = "~/CLionProjects/GooseTests/run-directory/"
source_dir = "~/CLionProjects/ALMaSS_all"
simulation_start_date = dt.date(2009, 1, 1)# we should check again that this is a right date, probably should be read from somewhere
simulation_start_date_ordinal=dt.date.toordinal(simulation_start_date)

# Forage data first
#forage_data=pd.read_csv(data_dir+"GooseFieldForageData.txt", sep='\t', header=0, parse_dates=['day'], dtype={'day': 'str'},date_parser=my_dateparser)
forage_data=pd.read_csv(data_dir+"GooseFieldForageData.txt", sep='\t', header=0, dtype={'day': np.int16})
# The field dayordinal has the current day counting from 1/1/0001
forage_data['dayordinal']=forage_data['day']+simulation_start_date_ordinal
# Useful function that parses the data 
my_dateparser=(lambda x: pd.to_datetime(x,unit='D', origin=simulation_start_date))
# The field 'daydate includes the date of the day for the data'
forage_data['daydate']=my_dateparser(forage_data['day'])
# A dictionary that will allow to map vegetation to habitat
# The key is a tuple of last_sown_veg, veg_phase, veg_type_chr, previous_crop
# Empty string means don't care
# The value is habitat (In current R file there different columns for each 
# species, but the resulting values are the same, so why?--> less code, less values is better)
veg_to_habitat = {
    # Grasses: check that none is missing
    ('PermanentGrassGrazed', 3, '', ''): 'Grass',
    ('PermanentGrassGrazed', 2, '', ''): 'Grass',
    ('PermanentGrassGrazed', 0, '', ''): 'Grass',
    ('PermanentGrassTussocky', 0, '', ''): 'Grass',
    ('PermanentGrassTussocky', 2, '', ''): 'Grass',
    ('CloverGrassGrazed1', 2, '', ''): 'Grass',
    ('CloverGrassGrazed1', 3, '', ''): 'Grass',
    ('CloverGrassGrazed2', 2, '', ''): 'Grass',
    ('OWinterWheatUndersown', 2, '', ''): 'Grass',
    ('OSeedGrass1', 3, '', ''): 'Grass',
    ('OSeedGrass1', 2, '', ''): 'Grass',
    ('OSeedGrass1', 0, '', ''): 'Grass',
    ('OSeedGrass2', 3, '', ''): 'Grass',
    ('OSeedGrass2', 2, '', ''): 'Grass',
    ('OSeedGrass2', 0, '', ''): 'Grass',
    ('SeedGrass2', 3, '', ''): 'Grass',
    ('SeedGrass2', 2, '', ''): 'Grass',
    ('SeedGrass2', 0, '', ''): 'Grass',
    ('SeedGrass1', 3, '', ''): 'Grass',
    ('SeedGrass1', 2, '', ''): 'Grass',
    ('SeedGrass1', 0, '', ''): 'Grass',
    ('OCloverGrassGrazed2', 0, '', ''): 'Grass',    
    ('OCloverGrassGrazed2', 2, '', ''): 'Grass', 
    ('OCloverGrassGrazed1', 0, '', ''): 'Grass', 
    ('OCloverGrassGrazed1', 2, '', ''): 'Grass', 
    ('OCloverGrassGrazed1', 3, '', ''): 'Grass', 
    ('CloverGrassGrazed1', 0, '', ''): 'Grass', 
    ('CloverGrassGrazed2', 0, '', ''): 'Grass', 
    }
 
