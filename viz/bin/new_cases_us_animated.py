import pandas as pd
import numpy as np
import datetime as dt
import os
import re
import tqdm

import plotly, plotly.graph_objects as go
import json

from collections import defaultdict

#-----------------------
# Load mapbox token
import yaml 
with open("../lib/mapbox-token.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
mapbox_access_token = cfg['key']
#-----------------------


def numpy_dt64_to_str(dt64):
    return pd.to_datetime(day).strftime('%b %d')


def read_jhu_data():
    basedir = '../../COVID-19/csse_covid_19_data/csse_covid_19_time_series'
    csvfile = f'{basedir}/time_series_covid19_confirmed_US.csv'
    df = pd.read_csv(csvfile, dtype={"FIPS": str})
    return df


def load_jhu_population_data():
    """ 
    Purpose: Load population and region data from the JHU data set and annotate
    with region information.
    Returns: a dataframe with the following columns: 
        Admin2, Province_State, Population, Region
    """
    base_loc = '../../'
    jhu_loc = f'{base_loc}/COVID-19'
    popcsv = f'{jhu_loc}/csse_covid_19_data/UID_ISO_FIPS_LookUp_Table.csv'
    df = pd.read_csv(popcsv, dtype={"FIPS": str})
    df = df[df.Country_Region == "US"]
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


def unroll_dates(df):
    """
    Purpose: Turn columns of dates into individual rows
    """
    rgx = re.compile(r'\d+/\d+/\d+')
    date_cols = [c for c in df.columns if rgx.search(c)]
    date_dts = [pd.to_datetime(d) for d in date_cols]
    date_cols_set = set(date_cols)

    all_dfs = []
    for col,dt in tqdm.tqdm(zip(date_cols, date_dts)):
        drop_these = date_cols_set - set([col])
        dff = df.drop(columns=drop_these).copy()
        dff['Last_Update'] = dt
        dff.rename(columns={col:'Confirmed'}, inplace=True)
        all_dfs.append(dff)

    df = pd.concat(all_dfs)
    return df

jhu_df = read_jhu_data()
popdf = load_jhu_population_data()
pop_yakutat = float(popdf[popdf.Admin2=="Yakutat plus Hoonah-Angoon"].Population) - \
              float(popdf[popdf.Admin2=="Hoonah-Angoon"].Population)
new_row = {'Admin2':'Yakutat', 'Province_State':'Alaska', 'Population':pop_yakutat}
popdf = popdf.append(new_row, ignore_index=True)
popdf.sort_values(['Province_State','Admin2'], inplace=True)
popdf.reset_index(drop=True,inplace=True)

jhu_pop_df = annotate_populations(jhu_df, popdf)

df = unroll_dates(jhu_pop_df)
df.reset_index(drop=True,inplace=True)
df.dropna(subset=['FIPS'],inplace=True)
df['FIPS'] = df['FIPS'].apply(lambda x: '%05d' % (int(float(x))))
df['NewCases'] = df.groupby(['Admin2','Province_State'])['Confirmed'].diff()
df['NewCases'].fillna(0,inplace=True)
df['Admin2'].fillna(df.Province_State,inplace=True)
df['NewCases7'] = df.groupby(['Province_State','Admin2'])['NewCases'].transform(lambda x: x.rolling(7).mean())
df['NewCases7Capita'] = df['NewCases7']*7/df['Population']*100000

# read US county geojson file
with open("../lib/county.geojson") as f:
  counties_json = json.load(f)


plot_var = "NewCases7Capita"
us_df = df[df.Last_Update > pd.to_datetime('3/1/2020')]
days = np.sort(us_df.Last_Update.unique())
plot_df = us_df[us_df.Last_Update == days[-1]]

# Make the very last day in the dataset
fig_data =go.Choroplethmapbox(geojson=counties_json, 
                              featureidkey='properties.GEOID',
                              locations=plot_df.FIPS, 
                              z=plot_df[plot_var],
                              zmin=0,
                              zmax=1000, #us_df[plot_var].max(),
                              customdata=plot_df[plot_var],
                              name="",
                              text=plot_df.Admin2.astype(str) + ", " + \
                                  plot_df["Province_State"].astype(str),
                              hovertemplate="%{text}<br>Cases/week/100K: %{customdata:.1f}",
                            #   colorbar=dict(outlinewidth=1,
                            #                outlinecolor="#333333",
                            #                len=0.9,
                            #                lenmode="fraction",
                            #                xpad=30,
                            #                xanchor="right",
                            #                bgcolor=None,
                            #                title=dict(text="Cases",
                            #                           font=dict(size=14)),
                            #                tickvals=[0,1,2,3,4,5,6],
                            #                ticktext=["1", "10", "100", "1K", "10K", "100K", "1M"],
                            #                tickcolor="#333333",
                            #                tickwidth=2,
                            #                tickfont=dict(color="#333333",
                            #                              size=12)),
                              colorscale="Blackbody", #ylgn,ylorrd,Jet
                              #reversescale=True,
                              marker_opacity=0.5,    #0.7
                              marker_line_width=1)   # 0

# set some basic style info
fig_layout = go.Layout(mapbox_style="light",
                       mapbox_zoom=3,
                       mapbox_accesstoken=mapbox_access_token,
                       mapbox_center={"lat": 37.0902, "lon": -95.7129},
                       margin={"r":0,"t":0,"l":0,"b":0},
                       plot_bgcolor=None)

# add a play and pause button
fig_layout["updatemenus"] = [dict(type="buttons",
                                  buttons=[dict(label="Play",
                                                method="animate",
                                                args=[None,
                                                      dict(frame=dict(duration=1000,
                                                                      redraw=True),
                                                           fromcurrent=True)]),
                                           dict(label="Pause",
                                                method="animate",
                                                args=[[None],
                                                      dict(frame=dict(duration=0,
                                                                      redraw=True),
                                                           mode="immediate")])],
                                  direction="left",
                                  pad={"r": 10, "t": 35},
                                  showactive=False,
                                  x=0.1,
                                  xanchor="right",
                                  y=0,
                                  yanchor="top")]


countfrom = (len(days)%7-1) % 7
days7 = [days[x] for x in range(countfrom, len(days), 7)]

usedays = days7

# a dictionary that describes the slider on the bototm
sliders_dict = dict(active=len(usedays) - 1,
                    visible=True,
                    yanchor="top",
                    xanchor="left",
                    currentvalue=dict(font=dict(size=20),
                                      prefix="Date: ",
                                      visible=True,
                                      xanchor="right"),
                    pad=dict(b=10, t=10),
                    len=0.875,
                    x=0.125, y=0,
                    steps=[]) # steps will be filled in later

fig_frames = []

for day in usedays: #usedays:
    plot_df = us_df[us_df.Last_Update == day]
    frame = go.Frame(data=[go.Choroplethmapbox(locations=plot_df.FIPS,
                                               z=plot_df[plot_var],
                                               customdata=plot_df[plot_var],
                                               name="",
                                               text=plot_df.Admin2.astype(str) + ", " + \
                                                    plot_df["Province_State"].astype(str),
                                               hovertemplate="%{text}<br>%{customdata:.1f}")],
                     name=numpy_dt64_to_str(day))
    fig_frames.append(frame)

    slider_step = dict(args=[[numpy_dt64_to_str(day)],
                             dict(mode="immediate",
                                  frame=dict(duration=300,
                                             redraw=True))],
                       method="animate",
                       label=numpy_dt64_to_str(day))
    sliders_dict["steps"].append(slider_step)

fig_layout.update(sliders=[sliders_dict])

# Plot the figure 
fig=go.Figure(data=fig_data, layout=fig_layout, frames=fig_frames)
#fig.show()
htmldir = '../html'
fig.write_html(f'{htmldir}/counties.html', auto_play=False, include_plotlyjs=False, full_html=False)

# notes: on Oct 31, Yakutat Alaska reported a negative value -> bad data, OK algorithm
