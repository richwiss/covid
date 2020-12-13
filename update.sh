#!/bin/bash

# Convenience script to update graphs daily

if [ -z ${VIRTUAL_ENV+x} ]; then
    echo "Error: Not in virtual environment: workon nlp"
    exit -1;
fi

# update data from JHU
BASEDIR=$(pwd)
    cd COVID-19 
    git remote update
    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u})
    if [ $LOCAL = $REMOTE ]; then
        echo "Up to date"
	cd "$BASEDIR"
    else
	# pull JHU data
	git pull
	cd "$BASEDIR"
	
	# update covidtracking data only if JHU data changed
	cd data/covidtracking
	./update.sh
	cd "$BASEDIR"
    fi


if [ -z ${COVIDDIR+x} ]; then
    export COVIDDIR="~/covid"
fi

export STATEDIR="${COVIDDIR}/states"

# create new graphs
if [ "$1" == "-f" ]; then
    python3 plots.py --states ALL --graph_directory "$COVIDDIR" --ignore_timestamp
else
    python3 plots.py --states ALL --graph_directory "$COVIDDIR" 
fi


# update tables
for state in Pennsylvania Florida Georgia New_Jersey New_York California North_Carolina Alabama Alaska Arizona Arkansas Colorado Connecticut Delaware District_of_Columbia Guam Hawaii Idaho Illinois Indiana Iowa Kansas Kentucky Louisiana Maine Maryland Massachusetts Michigan Minnesota Mississippi Missouri Montana Nebraska Nevada New_Hampshire New_Mexico North_Dakota Northern_Mariana_Islands Ohio Oklahoma Oregon  Rhode_Island South_Carolina South_Dakota Tennessee Texas Utah Vermont Virginia Virgin_Islands Washington West_Virginia Wisconsin Wyoming Puerto_Rico American_Samoa; do
    if [ "${STATEDIR}/${state}/${state}_table.html" -ot "${STATEDIR}/${state}/${state}_State_new_cases.png" ]; then
        python3 make_table_plotly.py -s "$state"
	    cp web/graphs.php ${STATEDIR}/${state}/graphs.php
	    chmod a+rX ${STATEDIR}/${state}
        chmod a+rX ${STATEDIR}/${state}/${state}_table.html 
        chmod a+rX ${STATEDIR}/${state}/index.php 
        chmod a+rX ${STATEDIR}/${state}/graphs.php 
    fi
done

if [ "${STATEDIR}/index.php" -ot "COVID-19/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv" ]; then
    python3 make_table_states.py
    chmod a+rX ${STATEDIR}/index.php ${STATEDIR}/table.html ${STATEDIR}/graphs.php
fi

