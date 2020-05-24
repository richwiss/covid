#!/bin/bash

# Convenience script to extract .csv/.txt from .html source

if [ -z ${VIRTUAL_ENV+x} ]; then
    echo "Error: Not in virtual environment: workon nlp"
    exit -1;
fi

if [ -z ${1+x} ]; then
    echo "Usage: update.sh <HTML>"
    exit -1
fi

JUPYTER_DATE=$1 ipython3 chesco.ipynb
