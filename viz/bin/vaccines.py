import pandas as pd
import plotly
import plotly.express as px

df = pd.read_csv('../../data/owid-covid-19-data/public/data/vaccinations/vaccinations.csv')
cc = pd.read_csv('../data/country_codes.csv')
codes = dict(zip(cc['COUNTRY'],cc['CODE']))
df = df[df.location.isin(codes)]
df['iso'] = df.location.apply(lambda x: codes[x])
df['dt'] = pd.to_datetime(df['date'])
df['date'] = df['dt'].dt.strftime("%Y-%m-%d")
df = df.loc[df.groupby('location').dt.idxmax()]
df.rename(columns = {"total_vaccinations_per_hundred": "pct vaccinated"},  inplace = True) 

#---------------------------------------------------------------

def generate_figure():
    fig = px.choropleth(df, locations="iso",
                        color="pct vaccinated",
                        hover_name="location",
                        hover_data=['date'],
                        projection='natural earth',
                        title='Percentage of people vaccinated',
                        range_color=(0,5),
                        color_continuous_scale=px.colors.sequential.Turbo)

    fig.update_layout(title=dict(font=dict(size=28),x=0.5,xanchor='center'),
                        margin=dict(l=60, r=60, t=50, b=50))
    #fig.update_layout(coloraxis_showscale=False)

    return fig


if __name__ == '__main__':
    fig = generate_figure()
    htmldir = '../html'
    fig.write_html(f'{htmldir}/vaccines.html', include_plotlyjs=False, full_html=False)
    