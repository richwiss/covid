#!/bin/bash

# Convenience script to update graphs daily

if [ -z ${VIRTUAL_ENV+x} ]; then
    echo "Error: Not in virtual environment: workon nlp"
    exit -1;
fi

if [ -z ${1+x} ]; then # no command-line: proceed as usual
    :  # do nothing
else
    if [ "$1" = "sleep" ]; then
	SECONDS=$(($(date -f - +%s- <<< $'tomorrow 06:00\nnow')0))
	if [ $SECONDS -gt 86400 ]; then # it's already after midnight
	    SECONDS=$(($(date -f - +%s- <<< $'today 06:00\nnow')0))
	fi
	echo "Sleeping $SECONDS seconds until 6am"
	# works in linux, not on a mac
	sleep $SECONDS
	date
    fi
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

python3 plots.py --states Illinois Kentucky Minnesota Missouri Texas Virginia --graph_directory "$COVIDDIR" --no_tqdm & 
pid1=$!

python3 plots.py --states Georgia Indiana Iowa Kansas Nebraska "North Carolina" Ohio Tennessee --graph_directory "$COVIDDIR" --no_tqdm &
pid2=$!

python3 plots.py --states Pennsylvania Florida Alabama Arkansas California Michigan Mississippi "New York" Oklahoma "Puerto Rico" Wisconsin "United States" --graph_directory "$COVIDDIR" --no_tqdm &
pid3=$!

python3 plots.py --states Alaska "American Samoa" Arizona Colorado Connecticut Delaware "District of Columbia" Guam Hawaii Idaho Louisiana Maine Maryland Massachusetts Montana Nevada "New Hampshire" "New Jersey" "New Mexico" "North Dakota" "Northern Mariana Islands" Oregon "Rhode Island" "South Carolina" "South Dakota" Utah Vermont "Virgin Islands" Washington "West Virginia" Wyoming --graph_directory "$COVIDDIR" --no_tqdm &
pid4=$!

echo -ne "Waiting on process 1\r"
wait $pid1
echo -ne "Waiting on process 2\r"
wait $pid2
echo -ne "Waiting on process 3\r"
wait $pid3
echo -ne "Waiting on process 4\r"
wait $pid4
echo "All processes complete.            "

# update tables
for state in Pennsylvania Florida Georgia New_Jersey New_York California North_Carolina Alabama Alaska Arizona Arkansas Colorado Connecticut Delaware District_of_Columbia Guam Hawaii Idaho Illinois Indiana Iowa Kansas Kentucky Louisiana Maine Maryland Massachusetts Michigan Minnesota Mississippi Missouri Montana Nebraska Nevada New_Hampshire New_Mexico North_Dakota Northern_Mariana_Islands Ohio Oklahoma Oregon  Rhode_Island South_Carolina South_Dakota Tennessee Texas Utah Vermont Virginia Virgin_Islands Washington West_Virginia Wisconsin Wyoming Puerto_Rico American_Samoa; do
    echo -ne "Building table: $state                    \r"
    if [ "${STATEDIR}/${state}/${state}_table.html" -ot "${STATEDIR}/${state}/${state}_State_new_cases.png" ]; then
        python3 make_table_plotly.py -s "$state"
	    cp web/graphs.php ${STATEDIR}/${state}/graphs.php
	    chmod a+rX ${STATEDIR}/${state}
        chmod a+rX ${STATEDIR}/${state}/${state}_table.html 
        chmod a+rX ${STATEDIR}/${state}/index.php 
        chmod a+rX ${STATEDIR}/${state}/graphs.php 
    fi
done

echo "Building tables: Completed                    "
if [ "${STATEDIR}/index.php" -ot "COVID-19/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv" ]; then
    python3 make_table_states.py
    chmod a+rX ${STATEDIR}/index.php ${STATEDIR}/table.html ${STATEDIR}/graphs.php
fi

BASEDIR=$(pwd)
    cd viz/bin
    ./update.sh
    cd "$BASEDIR"

date
