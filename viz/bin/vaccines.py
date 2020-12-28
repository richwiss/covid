# Environment used: dash1_8_0_env
import pandas as pd     #(version 1.0.0)
import plotly           #(version 4.5.0)
import plotly.express as px

import dash             #(version 1.8.0)
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

df = pd.read_csv('../../data/owid-covid-19-data/public/data/vaccinations/vaccinations.csv')
cc = pd.read_csv('../data/country_codes.csv')
codes = dict(zip(cc['COUNTRY'],cc['CODE']))
df = df[df.location.isin(codes)]
df['iso'] = df.location.apply(lambda x: codes[x])
df['dt'] = pd.to_datetime(df['date'])
df['date'] = df['dt'].dt.strftime("%Y-%m-%d")
df = df.loc[df.groupby('location').dt.idxmax()]
df.rename(columns = {"total_vaccinations_per_hundred": "vaccines per 100"},  inplace = True) 

#---------------------------------------------------------------

def generate_figure():
    fig = px.choropleth(df, locations="iso",
                        color="vaccines per 100",
                        hover_name="location",
                        hover_data=['date'],
                        projection='natural earth',
                        title='Vaccines administered per 100 people',
                        color_continuous_scale=px.colors.sequential.Plasma)

    fig.update_layout(title=dict(font=dict(size=28),x=0.5,xanchor='center'),
                        margin=dict(l=60, r=60, t=50, b=50))

    return fig


if __name__ == '__main__':
    fig = generate_figure()
    htmldir = '../html'
    fig.write_html(f'{htmldir}/vaccines.html', include_plotlyjs=False, full_html=False)
    