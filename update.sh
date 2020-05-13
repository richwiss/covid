#!/bin/bash

# Convenience script to update graphs daily

# update data from JHU
cd COVID-19
git pull
cd -
# create new graphs
jupyter nbconvert --to notebook --execute plots.ipynb --ExecutePreprocessor.timeout=-1 --ExecutePreprocessor.kernel_name=python3


# create tables
for state in $(ls states); do
    echo "Generating table for $state";
    python3 make_table.py -s $state
done

# be sure files are readable on the server
ssh ginger chmod -R a+rX /dropbox/richardw/Dropbox/covid/web/ /dropbox/richardw/Dropbox/covid/states/

