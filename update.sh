#!/bin/bash

# Convenience script to update graphs daily

# update data from JHU
cd COVID-19
git pull
cd -
# create new graphs
mkdir -p png
jupyter nbconvert --to notebook --execute plots.ipynb --ExecutePreprocessor.timeout=-1
# create tables
python3 make_table.py -s Pennsylvania

# be sure files are readable on the server
ssh ginger chmod -R a+rX /dropbox/richardw/Dropbox/covid/web/ /dropbox/richardw/Dropbox/covid/states/