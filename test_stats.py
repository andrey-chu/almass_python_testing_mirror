#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 21 15:00:12 2020

@author: andrey
"""
import pandas as pd
data_dir = '/data/au517882/CLionProjects/GooseTests/Goose_debug/'
energetics_data_logged=pd.read_csv(data_dir+"GooseEnergeticsData.txt", sep='\t', header=0)
debug_log = pd.read_csv(data_dir+"debuglog.csv", sep='\t', header=None)

