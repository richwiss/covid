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

date >> log
# create new graphs
for state in Pennsylvania Florida Georgia New_Jersey New_York California North_Carolina Alabama Alaska Arizona Arkansas Colorado Connecticut Delaware District_of_Columbia Guam Hawaii Idaho Illinois Indiana Iowa Kansas Kentucky Louisiana Maine Maryland Massachusetts Michigan Minnesota Mississippi Missouri Montana Nebraska Nevada New_Hampshire New_Mexico North_Dakota Northern_Mariana_Islands Ohio Oklahoma Oregon  Rhode_Island South_Carolina South_Dakota Tennessee Texas Utah Vermont Virginia Virgin_Islands Washington West_Virginia Wisconsin Wyoming; do
    #for state in $(ls states); do
    if [ "states/$state/index.php" -ot "COVID-19/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv" ]; then
        #TIMESTART=$(date +%s.%N)
        sstate=$(echo $state | perl -pe 's/_/ /g;')
        STATEPLOT="$sstate" ipython3 plots.ipynb
        python3 make_table_plotly.py -s "$state"
	cp web/graphs.php states/"$state"/graphs.php
        chmod -R a+rX states/"$state"
        #TIMEEND=$(date +%s.%N)
        #DURATION=$(echo "( $TIMEEND - $TIMESTART )" | bc -l ) 
        #echo "$DURATION $state" >> log
    fi
done

