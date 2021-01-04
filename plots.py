#!/usr/bin/env python
# coding: utf-8

# TODO: 
# - Cleanup/merge .sh scripts

# TODO: *** mapping only ***
# - Make US state-level map and county-level map for each page?
#   - state info needs abbreviations (e.g. AL, PA, GA)
#   - see https://towardsdatascience.com/choropleth-maps-101-using-plotly-5daf85e7275d
# - Fake FIPS data for merged counties (Utah, Alaska, Massachusettes)
# - Guam and Northern Mariana Islands (and maybe Virgin Islands) don't get mapped in county map
# - switch weekly_cases to mapbox?

import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
import datetime
import numpy as np
from tqdm import tqdm
from collections import defaultdict
import os
import re
import pathlib
import sys
import argparse
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

import covidtracking
import common
import jhu
import genstats

"""
Global variables
"""
# Directory setup
base_loc = '.'
## where population data is stored
population_loc = f'{base_loc}/data/resources'
## root directory of the JHU data repository
jhu_loc = f'{base_loc}/COVID-19'
series_loc = f'{jhu_loc}/csse_covid_19_data/csse_covid_19_time_series'
confirmed_csv = f'{series_loc}/time_series_covid19_confirmed_US.csv'

###########################################################################
# REWRITES
###########################################################################

def is_updated(state, ustate, statedir):
    state_stat_file = pathlib.Path(f'{statedir}/{ustate}/{ustate}_State_posneg.html')
    if state_stat_file.exists():
        state_stat_file_mtime = state_stat_file.stat().st_mtime
        csv_path = pathlib.Path(confirmed_csv)
        csv_path_mtime = csv_path.stat().st_mtime
        if csv_path_mtime < state_stat_file_mtime:
            print(f'Files up to date: {state:30}\r', end="")
            return True
    return False

def progress_update(use_tqdm, pbar, pid, label):
    """
    Helper function for showing onscreen progress while running
    """
    if use_tqdm:
        pbar.set_description(label)
    else:
        print(f"{pid:8} {label}")


def gen_state_plots(state, cdf, rdf, sdf, statedir, tempdir,
                    ignore_timestamp=False, use_tqdm=True):

    ustate = state.replace(' ','_')
    pid = os.getpid()

    # if not ignoring the timestamp, check it: return if up to date
    if (not ignore_timestamp) and is_updated(state, ustate, statedir):
        return

    outpath = pathlib.Path(f'{tempdir}/{ustate}')
    outpath.mkdir(parents=True, exist_ok=True)  # mkdir if it doesn't exist

    counties = set(cdf[cdf.Province_State==state].Admin2.unique())
    counties = set([c for c in counties if not (c.startswith('Out of') \
        or c.startswith('Unassigned'))])
    if len(counties) == 1:
        counties = set() # omit counties where there's only one (e.g. Guam)
    if state == 'Michigan':
        counties -= set(['Michigan Department of Corrections (MDOC)', 
                        'Federal Correctional Institution (FCI)'])

    regions = set(rdf[rdf.Province_State==state].Region.unique())

    wrapper = (lambda x: tqdm(x)) if use_tqdm else (lambda x: x)

    # COUNTIES
    pbar = wrapper(sorted(counties))
    for county in pbar:
        progress_update(use_tqdm, pbar, pid, f"{state}:{county:20}")
        create_graphs(cdf[(cdf.Admin2==county)&(cdf.Province_State==state)], output_directory=outpath)
                    
    # REGIONS
    pbar = wrapper(sorted(regions))
    for region in pbar:
        progress_update(use_tqdm, pbar, pid, f"{state}:{region:20}")
        create_graphs(rdf[(rdf.Region==region)&(rdf.Province_State==state)], output_directory=outpath)

    # STATE
    progress_update(use_tqdm, pbar, pid, f"{state}")
    create_graphs(sdf[(sdf.Province_State==state)], output_directory=outpath)

    print(f'--> Moving staged files: {state}')
    tempdir_state = pathlib.Path(tempdir, ustate)
    statedir_state= pathlib.Path(statedir, ustate)
    move_state_files(tempdir_state, statedir_state, extension='png', chmod=0o644)
    move_state_files(tempdir_state, statedir_state, extension='html', chmod=0o644)


def label_dataframe(df):
    """
    Purpose: Create a friendly label for this dataframe. Assume the
    dataframe has been isolated to a single county, region or state.
    """
    if 'Admin2' in df: # county-level data
        label = '%s County, %s' % tuple(df.iloc[0][['Admin2','Province_State']])
    elif 'Region' in df: # region-level data
        label = '%s Region, %s' % tuple(df.iloc[0][['Region','Province_State']])
    #elif df.iloc[0].Province_State == "United States":
    #    label = 'United States'
    else:
        label = '%s State' % tuple(df.iloc[0][['Province_State']])
    return label

## For a given data frame, plot all of the graphs #xxxx
def create_graphs(df, output='png', output_directory=None):
    """
    Start of rewrite. 
    """
    label = label_dataframe(df)

    if output == 'png':
        output = label.replace(' ','_') + '.png'
        output = output.replace(',','')
        if output_directory==None:
            output_directory='png'
        output = f"{output_directory}/{output}"
    else:
        output = 'inline'

    from plots_plotly import new_case_plotly, yellow_target_plotly, trending_plotly, trending2_plotly, posNeg_rate_plotly
    pngScale=1 #0.25
    new_case_plotly(df, label, days=7, output=output, pngScale=pngScale)    
    yellow_target_plotly(df, label, output=output, pngScale=pngScale)
    if 'slope_14' in df:
        trending_plotly(df, label, days=14, output=output, pngScale=pngScale)
    elif 'trend_14' in df:
        trending2_plotly(df, label, days=14, output=output, pngScale=pngScale)
    if ('positive' in df.columns): # covidtracking data
        posNeg_rate_plotly(df, label, days=7, output=output, pngScale=pngScale, clip_date='2020-03-15', 
                            tail_prune=True)


###########################################################################
# File manipulation

## helper to move files from staging to published
def move_state_files(olddir, newdir, extension='png', chmod=None):
    glob = f'*.{extension}'
    olddir = pathlib.Path(olddir)
    newdir = pathlib.Path(newdir)
    for olditem in olddir.iterdir():
        if olditem.is_dir():
            newitem = newdir.joinpath(olditem.name)
            # Be sure subdir exists in newdir
            pathlib.Path(newitem).mkdir(parents=True, exist_ok=True)
            allfiles=olditem.glob(glob)
            for onefile in allfiles:
                newpath = newitem.joinpath(onefile.name)
                onefile.rename(newpath)
                if chmod:
                    newpath.chmod(chmod)
        elif olditem.is_file():
            if olditem.name.endswith(f'.{extension}'):
                newitem = pathlib.Path(newdir, olditem.name)
                # Be sure subdir exists for newitem
                subdir = os.path.dirname(newitem)
                pathlib.Path(subdir).mkdir(parents=True, exist_ok=True)
                olditem.rename(newitem)
                if chmod:
                    newitem.chmod(chmod)


###########################################################################


###########################################################################
# Command-line parsing

## Set to all states if necessary
def set_statelist(states):
    if states == ['ALL']:
        states = list(common.state_d.values()) + list(common.territory_d.values())
    return states

def set_outdirs(coviddir):
    """
    Purpose: set yo the output directories for states/ and staging/
    Returns: the paths of the states/ and staging/ directories
    """
    statedir = pathlib.Path(coviddir, 'states')
    tempdir = pathlib.Path(coviddir, 'staging')
    # make the directories if theys doesn't exist
    pathlib.Path(statedir).mkdir(parents=True, exist_ok=True) 
    pathlib.Path(tempdir).mkdir(parents=True, exist_ok=True) 
    return (statedir, tempdir)

## Parse the command line
def parse_cmdline():
    """ Get command-line arguments """
    defaultdir = pathlib.Path(pathlib.Path.home(), "Desktop", "covid")

    parser = argparse.ArgumentParser(description='Build COVID graphs')
    parser.add_argument('--states', nargs='+', help='States to build a graph for', required=True)
    parser.add_argument('--ignore_timestamp', action='store_true', help="Force rebuilding of graphs.")
    parser.add_argument('--graph_directory', help='Output directory for staging and published graphs.', 
                        default=defaultdir)
    parser.add_argument('--no_trends', help="Disable trends for counties", action='store_true')
    parser.add_argument('--no_tqdm', action='store_true', help="Turn off tqdm")
    pargs = parser.parse_args()
    args = vars(pargs)

    if args['ignore_timestamp']: print("WARNING: Ignoring timestamp",file=sys.stderr)

    return args

###########################################################################
# One-off graphs
def one_off(cdf, rdf, sdf, state=None, county=None, region=None, outpath=None):
    if county is not None:
        create_graphs(cdf[(cdf.Province_State==state)&(cdf.Admin2==county)], output_directory=outpath)
    elif region is not None:
        create_graphs(rdf[(rdf.Province_State==state)&(rdf.Region==region)], output_directory=outpath)
    else:
        create_graphs(sdf[(sdf.Province_State==state)], output_directory=outpath)
###########################################################################
def read_data(clip_date=None):
    """
    Purpose: Read data sources from JHU and covidtracking.com
    Input: clip_date, a datetime object representing the earliest date to store
    Returns: 
      - cdf (dataframe with county-date rows)
      - ct_df (covidtracking data)
    """    
    (_, _, cdf) = jhu.read_annotated_jhu_data(omit_zero_counties=True)
    if clip_date:
        cdf = cdf[cdf['Last_Update'] >= clip_date].reset_index(drop=True)
    ct_df = covidtracking.get_data(trim=True, clip_date=clip_date)

    return (cdf, ct_df)

###########################################################################
def statedf_to_nationaldf(sdf, ct_df):
    """
    Purpose: Aggregate the state-level df (sdf) into a national-level df.
    Returns: A new national-level df
    """
    usdf = sdf.groupby(['Last_Update'])[['Confirmed','Population','positive','negative']].sum().reset_index()
    usdf['Province_State']="United States"

    genstats.gen_statistics(usdf, groupby=['Province_State'])
    usdf.sort_values(['Province_State','Last_Update'], inplace=True)
    usdf.reset_index(drop=True,inplace=True)
    covidtracking.augment(usdf, window=7, last_valid=max(ct_df.Last_Update))

    return usdf

###########################################################################
def countydf_to_statedf(cdf, ct_df):
    """
    Purpose: Aggregate the county-level df (cdf) into a state-level df and
      merge the covidtracking dataframe into this df.
    Returns: A new state-level df
    """
    sdf = cdf.groupby(['Last_Update','Province_State'])[['Confirmed','Population']].sum().reset_index()
    genstats.gen_statistics(sdf, groupby=['Province_State'])
    sdf.sort_values(['Province_State','Last_Update'], inplace=True)
    sdf.reset_index(drop=True,inplace=True)
    # note that this merge potentially adds junk data in the last rows as the covidtracking
    # data isn't always updated when the JHU data is updated.
    sdf = pd.merge(sdf, ct_df, how='left', on=['Last_Update', 'Province_State'])
    covidtracking.augment(sdf, window=7, last_valid=max(ct_df.Last_Update))

    return sdf
###########################################################################
def countydf_to_regiondf(cdf):
    """
    Purpose: Aggregate the county-level df (cdf) into a state-level df
    Returns: A new state-level df
    """
    rdf = cdf.groupby(['Last_Update','Region','Province_State'])[['Confirmed','Population']].sum().reset_index()
    genstats.gen_statistics(rdf, groupby=['Region'])
    rdf.sort_values(['Province_State','Region','Last_Update'], inplace=True)
    rdf.reset_index(drop=True,inplace=True)

    return rdf
###########################################################################
if __name__ == '__main__':
    args = parse_cmdline()
    states = set_statelist(args['states'])

    clip_date = pd.to_datetime('03/01/2020')
    (cdf, ct_df) = read_data(clip_date=clip_date)

    sdf = countydf_to_statedf(cdf, ct_df)
    usdf= statedf_to_nationaldf(sdf, ct_df)

    cdf = cdf[cdf['Province_State'].isin(states)].reset_index(drop=True)
    genstats.gen_statistics(cdf, groupby=['Admin2','Province_State'], no_trends=args['no_trends'])
    rdf = countydf_to_regiondf(cdf)

    delco = cdf[(cdf.Province_State=='Pennsylvania')&(cdf.Admin2=='Delaware')]
    pa = sdf[(sdf.Province_State=='Pennsylvania')]
    southeast = rdf[(rdf.Province_State=='Pennsylvania')&(rdf.Region=='South East')]

    coviddir = args['graph_directory']
    (statedir, tempdir) = set_outdirs(coviddir)

    ###########################################################################
    # quick fake
    #state = 'Pennsylvania'
    #county = 'Delaware'
    #region = 'South East'
    #outpath = f"{tempdir}/{state.replace(' ','_')}"

    #one_off(cdf,rdf,sdf,state=state,outpath=outpath)
    #gen_trend_original(cdf, ['Province_State','Admin2'], force=True)
    #one_off(cdf,rdf,sdf,state=state,county=county,outpath=outpath)
    #one_off(cdf,rdf,sdf,state=state,region=region,outpath=outpath)
    #breakpoint()
    ###########################################################################
    for state in states:
        statedf = usdf if (state == 'United States') else sdf
        gen_state_plots(state, cdf, rdf, statedf, statedir, tempdir,
                        ignore_timestamp=args['ignore_timestamp'],
                        use_tqdm=(not args['no_tqdm']))

###########################################################################


