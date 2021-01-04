import pandas as pd
import numpy as np
import datetime as dt
import os
import re
import tqdm

import plotly, plotly.graph_objects as go
import json

from collections import defaultdict

# not sure how packages are supposed to work... 
import sys
sys.path.append("../../") 
import jhu
import genstats
jhu.setup_dirs('../../')

from new_cases_us import load_counties

#-----------------------
# Load mapbox token
import yaml 
with open("../lib/mapbox-token.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
mapbox_access_token = cfg['key']
#-----------------------

def numpy_dt64_to_str(dt64):
    return pd.to_datetime(dt64).strftime('%b %d')

def generate_figure(us_df, counties_json):

    # get a list of the days in the dataframe
    days = np.sort(us_df.Last_Update.unique())
    plot_df = us_df[us_df.Last_Update == days[-1]]

    plot_var = 'percap_7'
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
    fig_layout.update(coloraxis_showscale=False)
    fig=go.Figure(data=fig_data, layout=fig_layout, frames=fig_frames)
    return fig


if __name__ == '__main__':
    (_,_,cdf) = jhu.read_annotated_jhu_data(omit_zero_counties=False, unmerge_counties=True)
    genstats.gen_statistics(cdf, groupby=['Admin2', 'Province_State'], no_trends=True)
    counties = load_counties(resolution='low')

    cdf = cdf[cdf.Last_Update > pd.to_datetime('3/1/2020')].reset_index(drop=True)

    fig = generate_figure(cdf, counties)
    htmldir = '../html'
    fig.write_html(f'{htmldir}/counties.html', auto_play=False, include_plotlyjs=False, full_html=False)
    #fig.show()

