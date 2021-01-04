#!/bin/bash

# Convenience script to update graphs daily

if [ -z ${VIRTUAL_ENV+x} ]; then
    echo "Error: Not in virtual environment: workon nlp"
    exit -1;
fi

# update data from OWID
BASEDIR=$(pwd)
    cd ../../data/owid-covid-19-data/
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
    fi

# update data from JHU
BASEDIR=$(pwd)
    cd ../../data/jhu/
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
    fi


if [ -z ${COVIDDIR+x} ]; then
    export COVIDDIR="~/covid"
fi

python3 vaccines.py
python3 new_cases.py
python3 new_cases_us.py
python3 new_cases_us_animated.py

chmod 644 ../html/*.html ../html/*.php

date
