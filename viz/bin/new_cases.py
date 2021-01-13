import pandas as pd
import plotly
import plotly.express as px

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

df = pd.read_csv('../../data/owid-covid-19-data/public/data/jhu/weekly_cases_per_million.csv')
cc = pd.read_csv('../data/country_codes.csv')
codes = dict(zip(cc['COUNTRY'],cc['CODE']))
df['dt'] = pd.to_datetime(df['date'])
most_recent = max(df.dt)
latest = df[df.dt == max(df.dt)]
countries = set(latest.columns)
keep = countries.intersection(set(codes))

dff = pd.DataFrame.from_dict(\
    {'dt': [most_recent] * len(keep),
    'date': [most_recent.strftime('%Y-%m-%d')] * len(keep),
    'location': sorted(keep),
    'iso': [codes[k] for k in sorted(keep)],
    'weekly_cases_per_million': [float(latest[k]) for k in sorted(keep)]})

dff['cases/100K'] = dff['weekly_cases_per_million']/10


#---------------------------------------------------------------

def generate_figure():
    fig = px.choropleth(dff, locations="iso",
                        color="cases/100K",
                        hover_name="location",
                        #hover_data=['date'],
                        hover_data={'date':True, 'cases/100K':':.1f','iso':False},
                        projection='natural earth',
                        title='New Cases/7 days/100K',
                        color_continuous_scale=px.colors.sequential.OrRd)

    fig.update_layout(title=dict(font=dict(size=28),x=0.5,xanchor='center'),
                        margin=dict(l=60, r=60, t=50, b=50))

    return fig


if __name__ == '__main__':
    fig = generate_figure()
    htmldir = '../html'
    fig.write_html(f'{htmldir}/weekly_cases.html', include_plotlyjs=False, full_html=False)
    
