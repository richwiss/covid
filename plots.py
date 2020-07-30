#!/usr/bin/env python
# coding: utf-8

# #### Todo
# 
# * incorporate delco data?
# 

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
import covidtracking
import common


"""
Global variables
"""
# Directory setup
base_loc = '.'
## where population data is stored
population_loc = f'{base_loc}/resources'
## root directory of the JHU data repository
jhu_loc = f'{base_loc}/COVID-19'
series_loc = f'{jhu_loc}/csse_covid_19_data/csse_covid_19_time_series'
confirmed_csv = f'{series_loc}/time_series_covid19_confirmed_US.csv'

###########################################################################
# Locality Selection

## Annotate the dataframe with region information, as available
def annotate_regions(df, region_df):
    """ Annotate the dataframe with the region, as available (PA, NY, MN, CA, GA) """
    region_map = defaultdict(lambda: np.nan)
    for d in region_df.to_dict('records'):
        region_map[(d['Province_State'], d['Admin2'])] = d['Region']
    df['Region'] = df[['Province_State', 'Admin2']].apply(lambda x: region_map[(x[0], x[1])], axis=1)

## Annotate the dataframe with populations
def annotate_populations(df, pop_df):
    """ Annotate the dataframe with populations """
    pop_map = defaultdict(lambda: np.nan)
    for d in pop_df.to_dict('records'):
        pop_map[d['Province_State'], d['Admin2']] = d['Population']
    df['Population'] = df.loc[:,['Province_State','Admin2']].apply(lambda x: pop_map[x[0], x[1]], axis=1)

## Discard counties with no cases (likely folded into a single county by JHU)
def omit_zero_counties(df):    
    # find which columns are dates and merge them
    rgx = re.compile(r'\d+/\d+/\d+')
    date_cols = [c for c in df.columns if rgx.search(c)]
    last_date = date_cols[-1]
    #filtered = df[df[last_date]>0]
    # don't throw away a place with no counties just because it has no cases
    filtered = df[(df[last_date]>0) | (df['Admin2'].isnull()) ]
    filtered.reset_index(drop=True, inplace=True)
    return filtered

# Calculate the population in the state from county populations
def state_populations(popdf):
    return dict(popdf.groupby(popdf.Province_State)['Population'].sum().items())

# Calculate the population in the region from county populations
def region_populations(popdf):
    """ for PA, calculate the population of each region """   
    return dict(popdf.groupby(popdf.Region)['Population'].sum().items())

## Remove and reorder the columns
def simplify_columns(df, date_cols=None):
    if not date_cols:
        # find which columns are dates
        rgx = re.compile(r'\d+/\d+/\d+')
        date_cols = [c for c in df.columns if rgx.search(c)]
    reorder = ['Admin2', 'Province_State', 'Country_Region', 'Combined_Key', 'Population'] + date_cols
    df = df[reorder]
    df.reset_index(drop=True, inplace=True)
    return df


## Merge and filter all data for just one state
def merge_state_series(sdf, popdf, state=None):
    """
    if state is None, the data frame needs to only contain one state
    """
    merged = pd.DataFrame()

    # verify there is only one state here --> if not, select it using the parameter
    states = set(sdf['Province_State'])
    assert len(states) >= 1
    if len(states) > 1:
        assert state is not None
        sdf = get_state_data(state, sdf)
    elif len(states) == 1:
        cur_state = states.pop()
        assert state == None or cur_state == state
        state = cur_state
            
    # verify there is at least one row here
    assert len(sdf) > 0

    # find which columns are dates and merge them
    rgx = re.compile(r'\d+/\d+/\d+')
    date_cols = [c for c in sdf.columns if rgx.search(c)]
    for date in date_cols:
        merged[date] = sdf.groupby(sdf['Province_State'])[date].sum()

    # sum the population of all of the counties
    merged['Population'] = sdf.groupby(sdf['Province_State'])['Population'].sum()

    # set the other metadata
    merged['Province_State'] = state
    merged['Admin2'] = 'All'  # instead of one county, it's all of them
    countries = set(sdf['Country_Region'])
    assert len(countries) == 1
    merged['Country_Region'] = countries.pop()
    merged['Combined_Key'] = f'{state} State'
    merged = simplify_columns(merged, date_cols)
    return merged


## Merge for just one region
def merge_region_series(sdf, popdf, region=None):
    merged = pd.DataFrame()

    # verify there is only one region here --> if not, select it using the paramater
    regions = set(sdf['Region'])
    assert len(regions) >= 1
    if len(regions) > 1:
        assert region is not None
        sdf = get_region_data(region, sdf)
    elif len(regions) == 1:
        cur_region = regions.pop()
        assert region == None or cur_region == region
        region = cur_region
    
    # verify there is at least one row here
    assert len(sdf) > 0

    # get the name of the state
    states = set(sdf['Province_State'])
    assert len(states) == 1
    state = states.pop()
        
    # find which columns are dates and merge them
    rgx = re.compile(r'\d+/\d+/\d+')
    date_cols = [c for c in sdf.columns if rgx.search(c)]
    for date in date_cols:
        merged[date] = sdf.groupby(sdf['Province_State'])[date].sum()

    # sum the population of all of the counties in the region
    merged['Population'] = sdf.groupby(sdf['Province_State'])['Population'].sum()
    merged['Province_State'] = state
    merged['Admin2'] = region # one region, not a county
    countries = set(sdf['Country_Region'])
    assert len(countries) == 1
    merged['Country_Region'] = countries.pop()
    merged['Combined_Key'] = f'{region} Region, {state}'
    merged = simplify_columns(merged, date_cols)
    return merged

## Filter all data for just one state, returns a new frame
def get_state_data(state, df):
    """
    Filter the data to include only the matching state
    """
    state_matches = pd.DataFrame(df[(df.Province_State==state)])
    return state_matches


## Filter all data for just one region, returns a new frame
def get_region_data(region, df):
    """
    Filter the data to include only the matching region
    """
    region_matches = pd.DataFrame(df[(df.Region==region)])
    return region_matches


## Filter all data for just one county, returns a new frame
def get_county_data(state, county, df):
    """
    1. Filter the data to include only the matching county/state
    2. Set a label (Combined_Key) to identify what we've selected in graphs
    3. Remove unneeded columns
    """
    merged = pd.DataFrame(df[(df.Province_State==state) & (df.Admin2==county)])
    merged['Combined_Key'] = f'{county} County, {state}'
    merged = simplify_columns(merged)
    return merged


def transpose(sdf):
    """ Convert the single-row time series JHU data to the table format """
    
    # Assumes a single row
    assert len(sdf) == 1
    
    # Save columns to a dictionary so we can retrieve later
    keys = sdf.to_dict('records')[0]
    rgx = re.compile(r'\d+/\d+/\d+')
    non_date_cols = [c for c in sdf.columns if not rgx.search(c)]
    sdf = sdf.drop(columns=non_date_cols)

    # Transpose the data
    df = sdf.transpose()

    # Copy column 0 into Confirmed (otherwise reseting the index deletes this)
    df['Confirmed'] = df[0]

    # Create Last_Update column from the index and standardize dates to noon each day
    df['Last_Update'] = df.index
    df.Last_Update = pd.to_datetime(df.Last_Update)
    df.Last_Update = df.Last_Update.dt.strftime('%m/%d/%Y')
    df.Last_Update = pd.to_datetime(df.Last_Update)
    
    # Restore the non-date values into the columns
    for col in non_date_cols:
        df[col] = keys[col]
    
    # Reindex
    df.reset_index(drop=True,inplace=True)

    # Reorder columns
    df = df[['Last_Update', 'Confirmed'] + non_date_cols]

    return df


def select_locality_series(sdf_all, popdf, query_type, query_state=None, query_region=None, query_county=None):
    # annotate regions and populations if not already done
    #if 'Region' not in sdf_all:
    #    annotate_regions(sdf_all, popdf)
    #if 'Population' not in sdf_all:
    #    annotate_populations(sdf_all, popdf)

    if query_type == 'State':
        df = get_state_data(query_state, sdf_all) 
        df = merge_state_series(df, popdf) 
    elif query_type == 'Region':
        df = get_state_data(query_state, sdf_all) 
        df = merge_region_series(df, popdf, region=query_region) 
    elif query_type == 'County':
        df = get_county_data(query_state, query_county, sdf_all) 
    
    return transpose(df)

###########################################################################


###########################################################################
# Perform calculations on the data

## Compute daily new cases
def daily_new_cases(df):
    """ given a DataFrame with a .Confirmed field, add a .New_Cases field that
    has new cases per day. """
    df['New_Cases'] = df.Confirmed.subtract(df.Confirmed.shift(1), fill_value=0)
    return df

## Compute average new cases
def average_new_cases(df, days, centered=False):
    """ this computes day the trailing average in the final day """
    """ compute the moving average over {days} days and add as day_avg_{days} to the df """
    field = f'day_avg_{days}'
    df[field] = df.New_Cases.rolling(window=14, min_periods=1, center=centered).mean()


## Calculate the average date from a list of dates (UNUSED)
def date_avg(dates):
  refdate = datetime.datetime(2019, 1, 1)
  return refdate + sum([date - refdate for date in dates], datetime.timedelta()) / len(dates)

## Find the best-fit line for a period of data
def fit(period):
    if len(period) == 1:
        return 0
    else:
        m, _ = np.polyfit(np.arange(len(period)), period, 1)
        return m

## Calculate the slope and number of days (in 2 weeks) 
def trend(df, days):
    """ 
    compute the trendline for the past {days} days as slope_{days} and
    the number of days within those {days} that the trend is worsening 
    (positive) or improving (negative) as {days}_trend
    """
    # Get the slope of the trend line for the past {days} days.
    sfield=f'slope_{days}'
    df[sfield] = df.New_Cases.rolling(window=days, min_periods=1).apply(fit)

    # Get the number of times the slope was positive in last {days} days.
    field = f'trend_{days}'
    df[field] = df[sfield].rolling(window=14, min_periods=14).apply(lambda x: (x>0).sum())

    return df




########################################
## Helpers to clip data at first case
def clip_at_zero_series(df):
    """
    Start the data the day before the first confirmed case
    """
    rgx = re.compile(r'\d+/\d+/\d+')
    date_cols = [c for c in df.columns if rgx.search(c)]
    drops = []
    for c in date_cols:
        sm = df[c].sum()
        if sm == 0:
            drops.append(c)
        elif sm > 0:
            break
    if len(drops) < len(date_cols):
        df = df.drop(columns=drops)
    return df

###########################################################################
# Pipeline
 
## For a given data frame, plot all of the graphs
def pipeline_helper(df, label, output, output_directory, use_plotly=True):
    df = df.sort_values(by='Last_Update', ignore_index=True)
    if output == 'png':
        output = label.replace(' ','_') + '.png'
        output = output.replace(',','')
        if output_directory==None:
            output_directory='png'
        output = f"{output_directory}/{output}"
    else:
        output = 'inline'

    has_covidtracking = ('positive' in df.columns)

    days = 14
    centered = False
    daily_new_cases(df) # add a new_cases column to the dataframe for the daily new cases
    average_new_cases(df, days, centered=centered) # adds average new cases in 'day_avg_{days}' column
    trend(df, days) # add slope and trend data
    if has_covidtracking:
        ct_days = 7
        covidtracking.augment(df, window=ct_days) # overwrite window value?


    if use_plotly:
        from plots_plotly import new_case_plotly, yellow_target_plotly, trending_plotly, posNeg_rate_plotly
        pngScale=0.25
        new_case_plotly(df, label, days=days, centered=centered, output=output, pngScale=pngScale)    
        yellow_target_plotly(df, label, output=output, pngScale=pngScale)
        trending_plotly(df, label, output=output, pngScale=pngScale)
        if has_covidtracking:
            posNeg_rate_plotly(df, label, days=ct_days, clip_date='2020-03-15', output=output, pngScale=pngScale)
    else:
        from plots_pylab import new_case_plot, yellow_target, trending
        new_case_plot(df, label, days=days, centered=centered, output=output)    
        plt.close()
        yellow_target(df, label, output=output)
        plt.close()
        trending(df, label, output=output)
        plt.close()
    
    return df


###########################################################################
# Functions to support time series data from JHU

def run_pipeline_series(all_sdf, popdf, query_type, query_state=None, query_region=None, query_county=None, output='inline', 
                output_directory=None, use_plotly=False, covidtracking_df=None):
    """
    Run pipeline on time_series data
    """
    assert query_type in ['State', 'County', 'Region']
    assert output in ['inline', 'png']

    df = select_locality_series(all_sdf, popdf, query_type, query_state, query_region, query_county)
    if query_type == 'State': # check is not None?
        ct_df = covidtracking.filter_by_state(covidtracking_df, query_state)
        df = pd.merge(df, ct_df)
    #print(f'{query_type} {query_state} {query_region} {query_county}')
    ckset = set(df.Combined_Key.values)
    assert len(ckset) == 1
    label = ckset.pop()

    return pipeline_helper(df, label, output, output_directory, use_plotly=use_plotly)

###########################################################################


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
                olditem.rename(newitem)
                if chmod:
                    newitem.chmod(chmod)


###########################################################################

#### Generate plots for the state
def generate_state_plots(state, popdf, all_sdf, statedir, tempdir,
                         use_plotly=True, ignore_timestamp=False,
                         covidtracking_df=None, use_tqdm=True):

    ustate = state.replace(' ','_')
    pid = os.getpid()

    if not ignore_timestamp:
        #state_stat_file = pathlib.Path(f'{statedir}/{ustate}/index.php')
        state_stat_file = pathlib.Path(f'{statedir}/{ustate}/{ustate}_State_posneg.html')
        
        if state_stat_file.exists():
            state_stat_file_mtime = state_stat_file.stat().st_mtime
            csv_path = pathlib.Path(confirmed_csv)
            csv_path_mtime = csv_path.stat().st_mtime
            if csv_path_mtime < state_stat_file_mtime:
                print(f'Files up to date: {state:30}\r', end="")
                return

    outpath = pathlib.Path(f'{tempdir}/{ustate}')
    outpath.mkdir(parents=True, exist_ok=True)  # mkdir if it doesn't exist

    counties = set()
    for county in set(all_sdf[all_sdf.Province_State==state].Admin2):
        if type(county) == float or county.startswith('Out of ') or county=="Unassigned":
            continue
        counties.add(county)

    regions = set(all_sdf.Region[(all_sdf.Region.notnull()) & (all_sdf.Province_State==state)])
    if state == 'New York' and 'New York City' in regions:
        # remove New York county -> already a New York region that is identical
        counties -= set(['New York'])
    if state == 'Michigan':
        counties -= set(['Michigan Department of Corrections (MDOC)', 'Federal Correctional Institution (FCI)'])

    state_df = get_state_data(state, all_sdf) 
    state_df = clip_at_zero_series(state_df)

    pbar = None
    if use_tqdm:
        wrapper = lambda x: tqdm(x)
    else:
        wrapper = lambda x: x

    # COUNTIES
    pbar = wrapper(sorted(counties))
    #pbar = [] # UNDO THIS
    for county in pbar:
        if use_tqdm:
            pbar.set_description(f"{state}:{county:20}")
        else:
            print(f"{pid:8} {state:20} {county:20}")

        run_pipeline_series(state_df, popdf, query_type="County",
                            query_state=state, query_county=county, 
                            output="png", output_directory=outpath,
                            use_plotly=use_plotly)

    # REGIONS
    pbar = wrapper(sorted(regions))
    for region in pbar:
        if use_tqdm: 
            pbar.set_description(f"{state}:{region:20}")
        else:
            print(f"{pid:8} {state:20} {region:20}")
        run_pipeline_series(state_df, popdf, query_type="Region",
                            query_state=state, query_region=region, 
                            output="png", output_directory=outpath,
                            use_plotly=use_plotly)

    # STATE
    run_pipeline_series(state_df, popdf, query_type="State",
                        query_state=state, output='png',
                        output_directory=outpath, use_plotly=use_plotly,
                        covidtracking_df=covidtracking_df)
    
    print(f'--> Moving staged files: {state}')
    tempdir_state = pathlib.Path(tempdir, ustate)
    statedir_state= pathlib.Path(statedir, ustate)
    move_state_files(tempdir_state, statedir_state, extension='png', chmod=0o644)
    move_state_files(tempdir_state, statedir_state, extension='html', chmod=0o644)


###########################################################################
# Command-line parsing

## Set to all states if necessary
def set_statelist(states):
    if states == ['ALL']:
        states = list(common.state_d.values()) + list(common.territory_d.values())
    return states

## Set the output directories
def set_outdirs(coviddir):
    statedir = pathlib.Path(coviddir, 'states')
    tempdir = pathlib.Path(coviddir, 'staging')
    pathlib.Path(tempdir).mkdir(parents=True, exist_ok=True) # make if it doesn't exist
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
    parser.add_argument('--no_tqdm', action='store_true', help="Turn off tqdm")
    pargs = parser.parse_args()
    args = vars(pargs)
    return args

###########################################################################
# Functions for loading data

## Load population and region data
## Note: Regions only supported for some states in the csv file

# Issues
# * 06-15-2020 : Dukes, MA and Nantucket, MA -> "Dukes and Nantucket"
# * Federal Correctional Institution (FCI), MI; Michigan Department of Corrections (MDOC), MI
#
# Possible fix: read population data from JHU data instead of my counties file

def load_population_data():
    """ load population and region data for counties in PA and other supported states """
    df = pd.read_csv(f'{population_loc}/county-populations.csv')
    return df

def load_jhu_population_data(convert=True):
    """ load population and region data for counties in PA and other supported states """
    df = pd.read_csv(f'{jhu_loc}/csse_covid_19_data/UID_ISO_FIPS_LookUp_Table.csv')
    if convert:
        return jhu_population_converter(df)
    return df

def jhu_population_converter(df):
    df = pd.DataFrame(df[df.Country_Region == "US"])
    region_df = pd.read_csv(f'{population_loc}/regions.csv')
    df.loc[(df.Province_State=='New York') & (df.Admin2=="New York City"), "Admin2"] = "New York"
    annotate_regions(df, region_df)
    #df = df.rename(columns={"Admin2": "County", "Province_State": "State"})
    df = df[["Admin2", "Province_State", "Population", "Region"]]

    df.reset_index(drop=True, inplace=True)
    return df

def get_series_data():
    """ read the series data in the JHU directory """
    df = pd.read_csv(confirmed_csv, dtype={"FIPS": str})
    return df
###########################################################################


###########################################################################
# One-off graphs
def one_off(all_sdf, popdf):
    #q_type='County'
    q_type='State'
    q_state='Montana'
    #q_state = 'New York'
    q_region='South East'
    #q_county='Delaware'
    q_county='New York'
    output='inline'
    outdir='png'
    use_plotly=True
    df = run_pipeline_series(all_sdf, popdf, q_type, query_state=q_state, query_county=q_county, 
                             query_region=q_region, output=output, output_directory=outdir, use_plotly=use_plotly)
    return df
###########################################################################



###########################################################################
def main():
    args = parse_cmdline()
    if args['ignore_timestamp']: print("WARNING: Ignoring timestamp")

    states = set_statelist(args['states'])
    coviddir = args['graph_directory']
    
    popdf = load_jhu_population_data()
    all_sdf = get_series_data()
    annotate_regions(all_sdf, popdf)
    annotate_populations(all_sdf, popdf)
    all_sdf = omit_zero_counties(all_sdf)

    ct_df = covidtracking.get_data(trim=True)
   
    (statedir, tempdir) = set_outdirs(coviddir)
    for state in states:
        generate_state_plots(state, popdf, all_sdf, statedir, tempdir,
                                ignore_timestamp=args['ignore_timestamp'],
                                covidtracking_df = ct_df,
                                use_tqdm=(not args['no_tqdm']))

    #df = one_off(all_sdf, popdf)
    return all_sdf, popdf
###########################################################################

if __name__ == '__main__':
    (all_sdf, popdf) = main()

    # some testing
    #query_type='State'
    #query_state='American Samoa'
    #df = select_locality_series(all_sdf, popdf, query_type, query_state=query_state)
    #popdf = load_jhu_population_data()
    #all_sdf = get_series_data()
    #annotate_regions(all_sdf, popdf)
    #annotate_populations(all_sdf, popdf)
    #all_sdf = omit_zero_counties(all_sdf)
    
