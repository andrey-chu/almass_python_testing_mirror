#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Binary version of the test file (generic)
It runs all the other tests
Should do the same thing as the jupyter notebook
Created on Mon Mar  2 14:56:09 2020

@author: Andrey Chuhutin
"""
import geopandas as gpd
import pandas as pd
import datetime as dt
import numpy as np
#import time
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import configparser, os

is_timed = True

species_names = ["barnacle", "greylag", "pinkfoot"]
geese_foods = ['grain', 'grass', 'maize']
if is_timed==True:
    is_timed_str = '_timed'
else:
    is_timed_str = ''
    
data_dir = "~/CLionProjects/GooseTests/run-directory1/"
source_dir = "~/CLionProjects/ALMaSS_all"
field_dir ="~/CLionProjects/GooseTests/ALMaSS_inputs"
additional_dir = "~/CLionProjects/data/"
# let us read the config data, it will be useful afterwards
CONFIG_PATH=data_dir+'TIALMaSSConfig.cfg'
with open(os.path.expanduser(CONFIG_PATH), 'r') as f:
    config_string = '[dummy_section]\n' + f.read()
config = configparser.ConfigParser(strict=False)
config.read_string(config_string)
xy_data=pd.read_csv(data_dir+"GooseXYDump.txt", sep='\t', header=0)
v_out=gpd.read_file(os.path.expanduser(additional_dir+"vejlerne-outline.gpkg"))
v_out_crs=v_out.to_crs(crs = "+proj=utm +zone=32 +ellps=GRS80 +units=m +no_defs")


