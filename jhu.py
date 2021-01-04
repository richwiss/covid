#!/usr/bin/env python
# coding: utf-8

# Tools to:
# - read in the confirmed cases from the JHU data set
# - read in the population data from the JHU
# - read in the locally customized region data
# - annotate the confirmed cases with population and region data
# - unroll the data so each date/location is its own row

import pandas as pd
import numpy as np
from collections import defaultdict
import tqdm
import re

###########################################################################
# Directory setup

def setup_dirs(base_loc='.'):
    global population_loc
    global jhu_loc
    global series_loc
    global confirmed_csv

    ## where population data is stored
    population_loc = f'{base_loc}/data/resources'
    ## root directory of the JHU data repository
    jhu_loc = f'{base_loc}/data/jhu/'
    series_loc = f'{jhu_loc}/csse_covid_19_data/csse_covid_19_time_series'
    confirmed_csv = f'{series_loc}/time_series_covid19_confirmed_US.csv'
setup_dirs()

###########################################################################

def clip_at_zero_series(df):
    """
    Purpose: Remove all days before the first confirmed case
    Input: Requires the dataframe in the original format with columns of dates
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
        df = df.drop(columns=drops, inplace=True)

###########################################################################

def load_jhu_population_data():
    """ 
    Purpose: Load population and region data from the JHU data set and annotate
    with region information.
    Returns: a dataframe with the following columns: 
        Admin2, Province_State, Population, Region
    """
    popcsv = f'{jhu_loc}/csse_covid_19_data/UID_ISO_FIPS_LookUp_Table.csv'
    df = pd.read_csv(popcsv, dtype={"FIPS": str})
    df = df[df.Country_Region == "US"]
    df = fix_yakutat_alaska(df)
    region_df = pd.read_csv(f'{population_loc}/regions.csv')
    # Rename the county for 'New York City' to be 'New York'
    #df.loc[(df.Province_State=='New York') & \
    #    (df.Admin2=="New York City"), "Admin2"] = "New York"
    annotate_regions(df, region_df)
    df = df[["Admin2", "Province_State", "Population", "Region"]]
    df.reset_index(drop=True, inplace=True)
    return df

###########################################################################
def fix_yakutat_alaska(df):
    """ Has no stand-alone population listed in the CSV """
    if len(df[(df.Province_State=='Alaska')&(df.Admin2=='Hoonah-Angoon')]) == 1 and \
       len(df[(df.Province_State=='Alaska')&(df.Admin2=='Yakutat plus Hoonah-Angoon')]) == 1 and \
       len(df[(df.Province_State=='Alaska')&(df.Admin2=='Yakutat')]) == 0:
        pop_yakutat = float(df[df.Admin2=="Yakutat plus Hoonah-Angoon"].Population) - \
                      float(df[df.Admin2=="Hoonah-Angoon"].Population)
        new_row = {'Admin2':'Yakutat', 'Province_State':'Alaska', 'Population':pop_yakutat}
        df = df.append(new_row, ignore_index=True)
    df.reset_index(drop=True,inplace=True)
    return df


def read_jhu_data():
    """ 
    Purpose: Load the time-series case counts data set.
    Returns: a dataframe with the following columns:
      - UID           : unknown usage
      - iso2          : 2-letter country code
      - iso3          : 3-letter country code
      - code3         : 3-digit country code
      - FIPS          : Federal Information Processing Standard code (US only)
      - Admin2        : County name (US only)
      - Province_State: Many countries support this
      - Country_Region: Country
      - Lat           : Latitude
      - Long_         : Longitude
      - Combined_Key  : pretty printed string for province/state, country
      - 1/22/20...    : one column for each day starting January 22, 2020
    """    
    df = pd.read_csv(confirmed_csv, dtype={"FIPS": str})
    # places with no county name get filled with the state name
    df['Admin2'].fillna(df.Province_State,inplace=True)
    return df

###########################################################################

def annotate_regions(df, region_df):
    """
    Purpose: Annotate the  confirmed case dataframe with the region, as available.
      -- As of Dec 2020, regions exist for PA, NY, MN, CA, GA.
    Side effect: Mutates the df dataframe to add a 'Region' column
    """
    region_map = defaultdict(lambda: np.nan)
    for d in region_df.to_dict('records'):
        region_map[(d['Province_State'], d['Admin2'])] = d['Region']
    df['Region'] = df[['Province_State', 'Admin2']].apply(lambda x: region_map[(x[0], x[1])], axis=1)

def annotate_populations(df, pop_df):
    """ 
    Purpose: Annotate the confirmed case dataframe with population information.
    Side effect: Mutates the df dataframe to add a 'Population' column
    """
    pop_map = defaultdict(lambda: np.nan)
    for d in pop_df.to_dict('records'):
        pop_map[d['Province_State'], d['Admin2']] = d['Population']
    df['Population'] = df.loc[:,['Province_State','Admin2']].apply(lambda x: pop_map[x[0], x[1]], axis=1)

###########################################################################

def drop_zero_counties(df):    
    """
    Purpose: Discard counties with no cases. These might have been folded into
    a single "county" by JHU. This is quite common in Utah. There are also some
    "counties" such as "Out of PA" or "Unassigned" that aren't really counties
    and are also removed. 
    As of January 2021, the counties removed were:
        ALASKA: Bristol Bay/Lake and Peninsula ("Bristol Bay plus Lake and Peninsula"), 
                Hoonah-Angoon (likely folded into Skagway)
        MASSACHUSETTS: Nantucket, Dukes ("Dukes and Nantucket")
        UTAH: Box Elder, Cache, Rich ("Bear River"), 
              Juab, Millard, Piute, Sanpete, Wayne ("Central Utah"),
              Carbon, Emery, Grand, Sevier ("Southeast Utah")
              Beaver, Garfield, Iron, Kane, Washington ("Southwest Utah")
              Daggett, Duchesne, Uintah ("TriCounty")
    
    Since totals from places like "Unassigned" may eventually get moved to 
    other counties, but are used in state totals, don't remove them unless
    there were *never* any cases there.

    Note that American Samoa has never had cases reported but is not removed 
    from this dataset with the special case.

    Returns: a new df with these counties removed.
    """
    # find which columns are dates and merge them
    rgx = re.compile(r'\d+/\d+/\d+')
    date_cols = [c for c in df.columns if rgx.search(c)]
    filtered = df[(df[date_cols].sum(axis=1)>0) | \
                (df['Admin2'].isnull()) | \
                (df['Province_State']=='American Samoa')]
    filtered.reset_index(drop=True, inplace=True)
    return filtered

###########################################################################
def unroll_dates(df):
    """
    Purpose: turn columns of dates into individual rows
    Input: a dataframe read from the JHU dataset already annotated with 
           population and region (if desired)
    Returns: a new dataframe with one row for each date/location
    """
    rgx = re.compile(r'\d+/\d+/\d+')
    date_cols = [c for c in df.columns if rgx.search(c)]
    date_dts = [pd.to_datetime(d) for d in date_cols]
    date_cols_set = set(date_cols)

    all_dfs = []
    for col,dt in zip(date_cols, date_dts):
        drop_these = date_cols_set - set([col])
        dff = df.drop(columns=drop_these).copy()
        dff['Last_Update'] = dt
        dff.rename(columns={col:'Confirmed'}, inplace=True)
        all_dfs.append(dff)

    df = pd.concat(all_dfs)
    df.reset_index(drop=True,inplace=True)

    return df


###########################################################################

def fix_merged_counties(rowdf):
    """
    Purpose: Copy Confirmed cases and Population statistics over
    to all of the counties that are part of a merged county.
    Note: This should be done only for mapping purposes and should be done
    before computing statistics.
    """
    regions = {('Southeast Utah', 'Utah'): ['Carbon', 'Emery', 'Grand', 'Sevier'],
        ('Central Utah', 'Utah'): ['Juab', 'Millard', 'Piute', 'Sanpete', 'Wayne'],
        ('Bear River', 'Utah'): ['Box Elder', 'Cache', 'Rich'],
        ('Southwest Utah', 'Utah'): ['Beaver', 'Garfield', 'Iron', 'Kane', 'Washington'],
        ('TriCounty', 'Utah'): ['Daggett', 'Duchesne', 'Uintah'],
        ('Weber-Morgan', 'Utah'): ['Weber', 'Morgan'],
        ('Dukes and Nantucket', 'Massachusetts'): ['Dukes', 'Nantucket']}

    columns = ['Confirmed', 'Population']

    for ((src, state), destinations) in tqdm.tqdm(regions.items()):
        for dst in destinations:
            for column in columns:
                rowdf.loc[(rowdf.Province_State==state)&(rowdf.Admin2==dst), column] = \
                    rowdf[rowdf.Admin2==src][column].to_list()


###########################################################################
def fix_FIPS(df):
    """
    Purpose: Fix the FIPS column so that it's a 5-digit, 0-padded string
    Side effect: Mutates the df.FIPS column
    """
    fn = lambda x: x if pd.isnull(x) else ('%05d' % (int(float(x))))
    df['FIPS'] = df['FIPS'].apply(fn)

###########################################################################
def read_annotated_jhu_data(omit_zero_counties=True, unmerge_counties=False):
    """
    Purpose: Read data sources from JHU and covidtracking.com
    """    
    popdf = load_jhu_population_data()
    jhudf = read_jhu_data()
    fix_FIPS(jhudf)
    annotate_regions(jhudf, popdf)
    annotate_populations(jhudf, popdf)
    if omit_zero_counties:
        jhudf = drop_zero_counties(jhudf)
    rowdf = unroll_dates(jhudf)
    if unmerge_counties:
        fix_merged_counties(rowdf)

    rowdf.sort_values(['Province_State','Admin2','Last_Update'], inplace=True)
    rowdf.reset_index(drop=True,inplace=True)

    return (popdf, jhudf, rowdf)

###########################################################################
def fix_counties(jhudf):
    """
    Purpose: For mapping, we need to give a z-value for counties that
    are folded together
    """
    pass

###########################################################################


if __name__ == '__main__':
    (popdf, jhudf, rowdf) = read_annotated_jhu_data()
