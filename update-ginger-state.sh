#!/bin/bash

# Convenience script to update graphs daily

if [ -z ${VIRTUAL_ENV+x} ]; then
    echo "Error: Not in virtual environment: workon nlp"
    exit -1;
fi

# update data from JHU
cd COVID-19
git pull
cd -

# convert script
jupyter nbconvert --to script plots.ipynb

state=$1
if [ "states/$state/index.php" -ot "COVID-19/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv" ]; then
    sstate=$(echo $state | perl -pe 's/_/ /g;')
    STATEPLOT="$sstate" ipython3 plots.py
    python3 make_table.py -s "$state"
    chmod -R a+rX states/"$state"
fi
