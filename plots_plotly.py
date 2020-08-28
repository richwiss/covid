import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Match plotly colors to plt colors, if desired
plt_color = {'blue': '#1f77b4', 'orange': '#ff7f0e', 'green': '#2ca02c', 'purple': '#9467bd', 'olive': '#bcbd22'}

###########################################################################
# Functions for plotly graphing

## Write the figures (png and html, as needed)
def write_figure_plotly(fig, output, title, description, pngScale=None):
    full_layout = go.Layout(
        title=title,
        showlegend=True,
    )

    hlegend = go.Layout(legend=dict(
    orientation="h",
    yanchor="bottom",
    y=1.02,
    xanchor="right",
    x=1))

    if output == 'inline':
        fig.update_layout(full_layout)
        fig.show()
    else:
        output = output.replace("'","").replace('.png', f'_{description}.png')
        fig.write_image(output, scale=pngScale)
        fig.update_layout(full_layout)
        fig.update_layout(hlegend)
        output = output.replace('.png', '.html')
        fig.write_html(output, include_plotlyjs=False, full_html=False)

########################################
## Daily new cases and 14-day moving average
def new_case_plotly(df, label, days=14, centered=False, output=None, pngScale=None):

    fig = go.Figure()
    fig.add_trace( # daily new cases
        go.Scatter(
            x = df.Last_Update,
            y = df.New_Cases,
            mode = 'lines+markers',
            name = 'Daily',
            line_color = plt_color['olive'],
            hovertemplate = '<b>%{y}</b>',
        )
    )

    fig.add_trace( # moving average
        go.Scatter(
            x = df.Last_Update,
            y = df[f'day_avg_{days}'],
            mode = 'lines',
            name = f'{days} day average',
            line_color = plt_color['blue'],
            hovertemplate = '<b>%{y:.1f}</b>',
        )
    )

    layout = go.Layout(
        xaxis_title="Date",
        yaxis_title="Positive tests",
        font=dict(
            size=12,
            color="#7f7f7f"
        ),
        showlegend=False,
        hovermode="x unified",
    )
    fig.update_layout(layout)
    
    title=f"New cases per day: {label}"
    write_figure_plotly(fig, output, title, 'new_cases', pngScale=pngScale)

########################################
## Days trending downward in 14 days
def trending_plotly(df, label, days=14, output=None, pngScale=None):
    #tfield = f'trend_{days}'
    sfield = f'slope_{days}'

    #formatted_dates = df['Last_Update'].apply(lambda x: x.strftime('%Y-%m-%d'))

    uptrend = df['trend_14']
    downtrend=df['trend_14']-14

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x = df.Last_Update,
            y = uptrend,
            name = f'Days trending up',
            marker_color = 'red',
            marker_line_width=1,
            offset=0,
            hovertemplate = '<b>%{y}</b>',
        ),
        secondary_y=False,

    )
    
    fig.add_trace(
        go.Bar(
            x = df.Last_Update,
            y = downtrend,
            name = f'Days trending down',
            marker_color = 'green',
            marker_line_width=1,
            offset=0,
            text = -downtrend,
            hovertemplate = '<b>%{text}</b>',
        ),
        secondary_y=False,
    )

    slope_range = max(abs(df[sfield]))*1.05
    
    secondary_min = -slope_range
    secondary_max = slope_range
    
    fig.add_trace(
        go.Scatter(
            x = df.Last_Update,
            y = df[sfield],
            name = 'Δ trend',
            line_color='black',
            hovertemplate = '<b>%{y:.2f}</b>',
        ),
        secondary_y=True,
    )

    layout = go.Layout(
        showlegend=False,  # updated for inline and html
        xaxis_title="Date",
        yaxis_title=f"Number of days",
        font=dict(
            size=12,
            color="#7f7f7f"
        ),
        hovermode="x unified",
        yaxis = {'range': [-14, 14], 'dtick':7},
        yaxis2= {'range': [secondary_min, secondary_max], 'showgrid': False}
    )

    fig.update_layout(layout)
    
    title=f"Two week trends: {label}"
    write_figure_plotly(fig, output, title, 'trend', pngScale=pngScale)



########################################
## Yellow target: 50 new cases over 14 days per 100K people
## Yellow target: 25 new cases over  7 days per 100K people

def yellow_target_plotly(df, label, output=None, pngScale=None):
    population = set(df.Population).pop()

    days = 7
    target = 25

    percap = df[f'day_avg_{days}']*100000 / population * days
    target_lst = [target] * len(df.Last_Update)

    fig = go.Figure()
    fig.add_trace(
            go.Scatter(
                x = df.Last_Update,
                y = percap,
                mode = 'lines+markers',
                name = f'{days} day per 100K',
                line_color = plt_color['blue'],
                hovertemplate = '<b>%{y:.1f}</b>',
            )
    )
    fig.add_trace(
        go.Scatter(
            x = df.Last_Update,
            y = target_lst,
            mode = 'lines',
            name = f'{target} cases per 100K',
            line_color = plt_color['orange'],
            hoverinfo = "none",
        )
    )

    layout = go.Layout(
        showlegend=False,  # updated for inline and html
        xaxis_title="Date",
        yaxis_title=f"Positive tests per capita",
        font=dict(
            size=12,
            color="#7f7f7f"
        ),
        hovermode="x unified",
    )
    fig.update_layout(layout)
    title = f"New cases/{days} days/100K people: {label}"
    write_figure_plotly(fig, output, title, 'yellow_target', pngScale=pngScale)

#####################################################################
# covidtracking.com graphs

########################################
## Positive/negative tests and positive test rate

########################################
## Days trending downward in 14 days
def posNeg_rate_plotly(df, label, days=14, clip_date=None, output=None, pngScale=None):
    if clip_date:
        df = df[df['Last_Update'] > clip_date]

    ptr_field = f'daily_positive_rate_{days}'
    ptr100_field = df[ptr_field] * 100

    daily_p = df.daily_positive
    daily_n = df.daily_negative

    total = daily_p + daily_n
    y_max = max(total)*1.05

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x = df.Last_Update,
            y = daily_p,
            name = f'Positive',
            marker_color = 'red',
            marker_line_width=1,
            offset=0,
            hovertemplate = '<b>%{y:8d}</b>',
        ),
        secondary_y=False,
    )
    
    fig.add_trace(
        go.Bar(
            x = df.Last_Update,
            y = daily_n,
            name = f'Negative',
            marker_color = 'green',
            marker_line_width=1,
            offset=0,
            hovertemplate = '<b>%{y:8d}</b>',
        ),
        secondary_y=False,
    )

    fig.update_layout(barmode='stack')

    fig.add_trace(
        go.Scatter(
            x = df.Last_Update,
            y = ptr100_field,
            name = f'{days}-day pct. positive',
            line_color='black',
            hovertemplate = '<b>%{y:.1f}%</b>',
        ),
        secondary_y=True,
    )

    layout = go.Layout(
        showlegend=False,  # updated for inline and html
        xaxis_title="Date",
        yaxis_title=f"Number of tests",
        font=dict(
            size=12,
            color="#7f7f7f"
        ),
        hovermode="x unified",

        yaxis = {'range': [0, y_max]},
        yaxis2= {'range': [0,100]}
    )

    fig.update_yaxes(title_text="positive test percentage", secondary_y=True)

    fig.update_layout(layout)
    
    title=f"Test results (covidtracking.com): {label}"
    write_figure_plotly(fig, output, title, 'posneg', pngScale=pngScale)
