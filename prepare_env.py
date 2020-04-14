#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The script that prepares the environment: copies files where they belong in order to 
be accessable in the repo
Created on Tue Apr 14 13:04:21 2020

@author: andrey
"""
import shutil 
import os
import errno
import distutils.dir_util
import zlib
import bz2
import lzma
import zipfile
data_dir = "~/CLionProjects/GooseTests/run-directory1/"
#source_dir = "~/CLionProjects/ALMaSS_all"
field_dir ="~/CLionProjects/GooseTests/ALMaSS_inputs"

data_dir_new =os.path.dirname(__file__)+"/rundir"
with open("filelistdata") as fp:
    datafileslist=fp.readlines()

datafileslist = [x.strip() for x in datafileslist] 

#source_dir_new =os.path.dirname(__file__)+ "/source"
field_dir_new =os.path.dirname(__file__)+ "/fielddir"
for j in [data_dir_new, field_dir_new]:
    try:
        os.mkdir(j)
        break
    except OSError as error:
            
        if error.errno != errno.EEXIST:
            raise
        else:
                print(j+" Directory exists: Ignoring")
        pass
    
for i in datafileslist:
    if i == "GooseFieldForageData.txt":
        cwd_s = os.getcwd()
        os.chdir(os.path.expanduser(data_dir+"/"))
        zipObj = zipfile.ZipFile(os.path.expanduser(data_dir_new+"/"+i+".gz"), 'w', compression=zipfile.ZIP_LZMA)
        zipObj.write(os.path.expanduser(i))
        zipObj.close()
        os.chdir(cwd_s)
    else:
        
        shutil.copy2(os.path.expanduser(data_dir+"/"+i), data_dir_new)
#distutils.dir_util.copy_tree(os.path.expanduser(source_dir), source_dir_new)
distutils.dir_util.copy_tree(os.path.expanduser(field_dir), field_dir_new)


