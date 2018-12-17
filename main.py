import os
import numpy as np
import pandas as pd
import requests
from datetime import datetime as dt
from datetime import timedelta

# plotly imports
import plotly.offline as pyo
import plotly.graph_objs as go

# dash imports
import dash
import dash_auth
import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State

# Authentication token
token = os.getenv('STREAMHOSTER')

# Credentials
username_secret = os.getenv('STREAMHOSTER_USER')
password_secret = os.getenv('STREAMHOSTER_PASS')
USERNAME_PASSWORD_PAIRS = [[username_secret,password_secret]]

# Initialize app
app = dash.Dash()
auth = dash_auth.BasicAuth(app,USERNAME_PASSWORD_PAIRS)
server = app.server

# Function returns a pandas data frame of Streamhoster data acquired through API 
def __StreamhosterDataFetcher__(start_time, end_time, media_key=None):
    TOKEN = token
    URL = 'https://api.streamhoster.com/reports/service-segments'
    payload = {'startTime': start_time, 'endTime': end_time, 'segmentNames': 'm'}
    r = requests.get(URL, params=payload, headers={'Authorization': 'Basic %s' %  TOKEN})
    data = r.json()
    df = pd.DataFrame({'mediakey': [], 'views': [], 'uniques': [], 'dataTransferGB': []})
    
    for i in data['services'][0]['m']:
        df = df.append({'mediakey': i['key'], 'views': i['totals']['views'], 'uniques': i['totals']['uniques'], 'datatransferGB': i['totals']['dataTransferGB']}, ignore_index=True)

    return df.sort_values(by=['views'], ascending=False)

today = dt.today().date()
tenDaysAgo = dt.today().date() - timedelta(days=10)

df = __StreamhosterDataFetcher__(tenDaysAgo.strftime('%Y%m%d'),today.strftime('%Y%m%d'))

data_views = [go.Bar(
            x=df['mediakey'].tolist(),
            y=df['views']
)]

data_uniques = [go.Bar(
            x=df['mediakey'].tolist(),
            y=df['uniques']
)]

app.layout = html.Div([

        html.H1('Streamhoster Dashboard'),

        html.Div([
        html.Label('Media Key: '),        
        dcc.Input(id='mediakeyinput',
                value='',
                type='text'),
        ], style={'padding':10, 'display':'inline-block'}
        ),
        
        html.Div([
        html.Label('Date Range: '),
        dcc.DatePickerRange(id='daterangeinput',
                        start_date=tenDaysAgo,
                        end_date=today,
                        max_date_allowed=dt.today()),
        ], style={'padding':10}
        ),

        html.Button(id='submit-button',
            n_clicks=0,
            children='Submit',
            style={'fontSize':18, 
                    'padding':15}
        ),

        html.Div([
        
        dcc.Graph(id='views',
            figure={
                    'data':data_views,
                    'layout':{'height':600, 
                                'width':1000, 
                                'yaxis':{'title':'Media Views'}, 
                                'margin':{'b':180}    
                    }
            }
            , style={'width':'50%'
                            ,'overflowX':'scroll'
                            ,'float':'left'
                    }
                ),

        dcc.Graph(id='uniques',
            figure={'data':data_uniques,
                    'layout':{'height':600, 
                                'width':1000, 
                                'yaxis':{'title':'Unique viewers'}, 
                                'margin':{'b':180}}
                    }, style={'width':'50%',
                                'overflowX':'scroll'})
        ])

])


# callback functions to dynamically update graphs when inputs are changed

@app.callback(Output('views','figure'),
            [Input('submit-button','n_clicks')],
            [State('mediakeyinput','value'),
                State('daterangeinput','start_date'),
                State('daterangeinput','end_date')])
def update_figure_views(n_clicks,media_key,daterangestart,daterangeend):
    # strip date from datetime and convert to string format
    daterangestart_input = dt.strptime(daterangestart,'%Y-%m-%d')
    daterangestart_string = dt.strftime(daterangestart_input,'%Y%m%d')

    daterangeend_input = dt.strptime(daterangeend,'%Y-%m-%d')
    daterangeend_string = dt.strftime(daterangeend_input,'%Y%m%d')

    # call StreamhosterDataFetcher for updated data
    new_data = __StreamhosterDataFetcher__(daterangestart_string, daterangeend_string)

    # filter to media key wildcard search
    if media_key == '':
        filtered_df = new_data
    else:
        filtered_df = new_data[new_data['mediakey'].str.contains(media_key)]

    traces = []

    traces.append(go.Bar(
            x = filtered_df['mediakey'].tolist(),
            y = filtered_df['views']
    ))

    layout = {'height':600, 'width':1000, 'yaxis':{'title':'Media Views'}, 'margin':{'b':160}}

    return {'data': traces,'layout':layout}

@app.callback(Output('uniques','figure'),
            [Input('submit-button','n_clicks')],
            [State('mediakeyinput','value'),
                State('daterangeinput','start_date'),
                State('daterangeinput','end_date')])
def update_figure_unique_viewers(n_clicks,media_key,daterangestart,daterangeend):
    daterangestart_input = dt.strptime(daterangestart,'%Y-%m-%d')
    daterangestart_string = dt.strftime(daterangestart_input,'%Y%m%d')

    daterangeend_input = dt.strptime(daterangeend,'%Y-%m-%d')
    daterangeend_string = dt.strftime(daterangeend_input,'%Y%m%d')

    new_data = __StreamhosterDataFetcher__(daterangestart_string, daterangeend_string)

    if media_key == '':
        filtered_df = new_data
    else:
        filtered_df = new_data[new_data['mediakey'].str.contains(media_key)]

    traces = []

    traces.append(go.Bar(
            x = filtered_df['mediakey'].tolist(),
            y = filtered_df['uniques']
    ))

    layout = {'height':600, 
                'width':1000, 
                'yaxis':{'title':'Unique Viewers'}, 
                'margin':{'b':160}
    }

    return {'data': traces, 'layout': layout}

if __name__ == '__main__':
    app.run_server()