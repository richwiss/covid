#!/bin/bash

# Convenience script to update graphs daily

# update data from JHU
cd COVID-19
git pull
cd -
# create new graphs
mkdir -p png
jupyter nbconvert --to notebook --execute paplot.ipynb --ExecutePreprocessor.timeout=-1
# create table
mkdir -p web
python3 make_table.py > web/table.html 

# be sure files are readable on the server
ssh water chmod -R a+rX Dropbox/covid/web/