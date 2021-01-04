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

# not sure how packages are supposed to work... 
import sys
sys.path.append("../../") 
import jhu
import genstats
jhu.setup_dirs('../../')

#------------------------------------------------------
import yaml #(pip install pyyaml)
with open("../lib/mapbox-token.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
mapbox_access_token = cfg['key']
#-------------------------------------------------------

def load_counties(resolution=None):
    import json
    if resolution == None or resolution == 'low':
        counties = json.load(open('../lib/cb_2018_us_county_20m.geojson')) 
    elif resolution == 'high':
        counties = json.load(open('../lib/cb_2018_us_county_5m.geojson')) 
    elif resolution == 'orig':
        counties = json.load(open('../lib/county.geojson'))
    return counties

def generate_figure(dff, counties):
    #median = df2['percap_7'].median()
    fig = px.choropleth_mapbox(dff, geojson=counties, locations='FIPS', color='percap_7',
                           featureidkey='properties.GEOID',  # if using county.geojson
                           # color_continuous_midpoint=median,  # not sure why this doesn't work
                           color_continuous_scale=px.colors.diverging.curl, #px.colors.sequential.Jet,
                           mapbox_style="carto-positron",
                           zoom=3, center = {"lat": 37.0902, "lon": -95.7129},
                           opacity=0.5,
                           range_color=(0, 1000),
                           labels={'percap_7':'cases/7 days/100K'},
                           hover_name="Combined_Key",
                           hover_data={'percap_7':':.1f', 'FIPS':False},
                           title='New cases/7 days/100K people',
                          )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    
    return fig

if __name__ == '__main__':
    (_,_,cdf) = jhu.read_annotated_jhu_data(omit_zero_counties=False, unmerge_counties=True)
    genstats.gen_statistics(cdf, groupby=['Admin2', 'Province_State'], no_trends=True)
    counties = load_counties(resolution='high')

    # delete everything except for the last day in the dataframe
    most_recent = cdf.Last_Update.max()
    cdf = cdf[cdf.Last_Update==most_recent].reset_index(drop=True)

    fig = generate_figure(cdf, counties)
    htmldir = '../html'
    fig.write_html(f'{htmldir}/weekly_cases_us.html', include_plotlyjs=False, full_html=False)
    #fig.show()
