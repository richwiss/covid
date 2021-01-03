import pandas as pd
import plotly
import plotly.express as px

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import numpy as np
from collections import defaultdict
import re

#------------------------------------------------------delete this section and add your own mapbox token below
import yaml #(pip install pyyaml)
with open("../lib/mapbox-token.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
mapbox_access_token = cfg['key']
#-------------------------------------------------------

filename = '../../COVID-19/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv'
df = pd.read_csv(filename)
df = df.dropna(subset=['FIPS'])
df['FIPS'] = df['FIPS'].apply(lambda x: '%05d' % (int(x)))

#df['FIPS'] = df['FIPS'].astype(int, errors='ignore')

# weekly cases 
rgx = re.compile(r'\d+/\d+/\d+')
date_cols = [c for c in df.columns if rgx.search(c)]
dates = dict(zip([pd.to_datetime(x) for x in date_cols], date_cols))
last_eight_days = [dates[x] for x in sorted(dates)[-8:]]
df['last_7'] = df[last_eight_days[-1]] - df[last_eight_days[0]]
#to_drop = set(dates.values()) - set(eight_days)
#df.drop(to_drop, axis=1,inplace=True)
#df.drop(dates.values(), axis=1,inplace=True)
dff = df[['FIPS','Province_State','Admin2','Combined_Key', 'last_7']]

# dff = pd.DataFrame.from_dict(\
#     {'dt': [most_recent] * len(keep),
#     'date': [most_recent.strftime('%Y-%m-%d')] * len(keep),
#     'location': sorted(keep),
#     'iso': [codes[k] for k in sorted(keep)],
#     'weekly_cases_per_million': [float(latest[k]) for k in sorted(keep)]})

# #---------------------------------------------------------------

base_loc = '../../'
## where population data is stored
population_loc = f'{base_loc}/data/resources'
## root directory of the JHU data repository
jhu_loc = f'{base_loc}/COVID-19'

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
    region_df = pd.read_csv(f'{population_loc}/regions.csv')
    # Rename the county for 'New York City' to be 'New York'
    df = df[["Admin2", "Province_State", "Population"]]
    df.reset_index(drop=True, inplace=True)
    return df

## Annotate the dataframe with populations
def annotate_populations(df, pop_df):
    """ 
    Purpose: Annotate the dataframe with population information.
    Side effect: Mutates the df dataframe to add a 'Population' column
    """
    df = df.copy()
    pop_map = defaultdict(lambda: np.nan)
    for d in pop_df.to_dict('records'):
        pop_map[d['Province_State'], d['Admin2']] = d['Population']
    df['Population'] = df.loc[:,['Province_State','Admin2']].apply(lambda x: pop_map[x[0], x[1]], axis=1)
    return df

def load_counties():
    import json
    counties = json.load(open('../lib/county.geojson'))
    return counties


def generate_figure(dff, counties):
    fig = px.choropleth_mapbox(dff, geojson=counties, locations='FIPS', color='last_7_percap',
                           #color_continuous_scale=px.colors.sequential.OrRd,
                           featureidkey='properties.GEOID',  # if using county.geojson
                           color_continuous_scale=px.colors.sequential.Jet,
                           mapbox_style="carto-positron",
                           zoom=3, center = {"lat": 37.0902, "lon": -95.7129},
                           opacity=0.5,
                           range_color=(0, 1000),
                           labels={'last_7_percap':'weekly new cases'},
                           hover_name="Combined_Key",
                           title='Weekly cases per 100K',
                          )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return fig

if __name__ == '__main__':
    popdf = load_jhu_population_data()
    pop_yakutat = float(popdf[popdf.Admin2=="Yakutat plus Hoonah-Angoon"].Population) - \
                  float(popdf[popdf.Admin2=="Hoonah-Angoon"].Population)
    new_row = {'Admin2':'Yakutat', 'Province_State':'Alaska', 'Population':pop_yakutat}
    popdf = popdf.append(new_row, ignore_index=True)
    popdf.sort_values(['Province_State','Admin2'], inplace=True)
    popdf.reset_index(drop=True,inplace=True)
    
    counties = load_counties()
    df2 = annotate_populations(dff, popdf)
    df2['last_7_percap'] = df2['last_7']/(df2['Population']/100000)

    fig = generate_figure(df2, counties)
    htmldir = '../html'
    fig.write_html(f'{htmldir}/weekly_cases_us.html', include_plotlyjs=False, full_html=False)
    #fig.show()

# remove 0s and/or fix utah
