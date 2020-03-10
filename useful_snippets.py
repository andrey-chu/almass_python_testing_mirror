# -*- coding: utf-8 -*-

#forage_data['start']=simulation_start_date
my_dateparser=(lambda x: pd.to_datetime(x,unit='days')) ## Parsing the timedeltas in days with lambda function
timeshifts = my_dateparser(forage_data['day'])
forage_data['dates']=forage_data['start']+timeshifts ## Not vectorized: is there a better way?