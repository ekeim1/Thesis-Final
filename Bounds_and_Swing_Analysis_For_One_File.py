# import needed packages
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
from datetime import datetime as dt
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash.exceptions import PreventUpdate
import base64
import io
import textwrap

app = dash.Dash(__name__) # create app; also uses assets folder for stylesheets

# app layout
app.layout = html.Div([
    # title
    html.Div([
        html.H1(children='Winterthur Bounds and Swing Analysis Interface', style={'textAlign': 'center',"margin-bottom": "0px"}),
        html.H2(children='for One File', style={'textAlign': 'center',"margin-top": "0px"})
    ],style={"margin-bottom": "25px"}),

    # uploads data files
    html.Div([
        html.H4(children='Upload data file (.pm2 file supported):'),
        dcc.Upload(
            html.Button('Upload Data File'),
            id='upload-data', style={'display': 'inline-block'}
        ),
        # output selected data file filename
        html.Div(id='output-data-upload', style={'display': 'inline-block'}),
    ],className="pretty_container twelve columns"),

    # select start date and end date for the overall period to examine
    # select months
    html.Div([
        html.H4('Date Range Selection:'),
        # start date selector
        html.Div([
            html.H6('Select start date (year, month, day, hour, minute):'),
            html.Div([
                html.Div([
                    dcc.Input(id='startDateYear', value=2013, type='number')
                ]),
                html.Div([
                    dcc.Dropdown(id='startDateMonth',
                                 options=[{'label': 'January', 'value': 1}, {'label': 'February', 'value': 2},
                                          {'label': 'March', 'value': 3}, {'label': 'April', 'value': 4},
                                          {'label': 'May', 'value': 5}, {'label': 'June', 'value': 6},
                                          {'label': 'July', 'value': 7}, {'label': 'August', 'value': 8},
                                          {'label': 'September', 'value': 9}, {'label': 'October', 'value': 10},
                                          {'label': 'November', 'value': 11}, {'label': 'December', 'value': 12}],
                                 value=7)
                ],className="two columns"),
                html.Div([
                    dcc.Dropdown(
                        id='start-day-dropdown',
                        options=[{'label': i, 'value': i} for i in range(1, 32)],
                        placeholder='Select end day:',
                        value=9
                    )
                ],className="two columns"),
                html.Div([
                    dcc.Dropdown(
                        id='start-hour-dropdown',
                        options=[{'label': i, 'value': i} for i in range(0, 24)],
                        placeholder='Select start hour:',
                        value=14
                    )
                ],className="two columns"),
                html.Div([
                    dcc.Dropdown(
                        id='start-minute-dropdown',
                        options=[{'label': i, 'value': i} for i in range(0, 60)],
                        placeholder='Select start minute:',
                        value=45
                    )
                ],className="two columns"),
            ],className='row flex-display')
        ]),

        # end date selector
        html.Div([
            html.H6('Select end date (year, month, day, hour, minute):'),
            html.Div([
                html.Div([
                    dcc.Input(id = 'endDateYear', value = dt.now().year, type = 'number')
                ]),
                html.Div([
                    dcc.Dropdown(id='endDateMonth',
                             options=[{'label': 'January', 'value': 1}, {'label': 'February', 'value': 2},
                                      {'label': 'March', 'value': 3}, {'label': 'April', 'value': 4},
                                      {'label': 'May', 'value': 5}, {'label': 'June', 'value': 6},
                                      {'label': 'July', 'value': 7}, {'label': 'August', 'value': 8},
                                      {'label': 'September', 'value': 9}, {'label': 'October', 'value': 10},
                                      {'label': 'November', 'value': 11}, {'label': 'December', 'value': 12}],
                             value=dt.now().month),
                ],className="two columns"),
                html.Div([
                    dcc.Dropdown(
                        id='end-day-dropdown',
                        options=[{'label':i, 'value':i} for i in range(1,32)],
                        placeholder='Select end day:',
                        value=dt.now().day
                    ),
                ],className="two columns"),
                html.Div([
                    dcc.Dropdown(
                        id='end-hour-dropdown',
                        options=[{'label':i, 'value':i} for i in range(0,24)],
                        placeholder='Select end hour:',
                        value = dt.now().hour
                    ),
                ],className="two columns"),
                html.Div([dcc.Dropdown(
                        id='end-minute-dropdown',
                        options=[{'label':i, 'value':i} for i in range(0,60)],
                        placeholder='Select end minute:',
                        value=dt.now().minute)
                ],className = 'two columns'),
            ],className='row flex-display'),
        ]),
        # select months
        html.H6('Select months to analyze within the overall range:'),
        html.Div([dcc.Dropdown(id='monthsToAnalyze',
                 options=[{'label': 'January', 'value': 1}, {'label': 'February', 'value': 2},
                          {'label': 'March', 'value': 3}, {'label': 'April', 'value': 4},
                          {'label': 'May', 'value': 5}, {'label': 'June', 'value': 6},
                          {'label': 'July', 'value': 7}, {'label': 'August', 'value': 8},
                          {'label': 'September', 'value': 9}, {'label': 'October', 'value': 10},
                          {'label': 'November', 'value': 11}, {'label': 'December', 'value': 12}],
                 value = [1,2,3,4,5,6,7,8,9,10,11,12],
                 multi = True
        )],className='ten columns'),
        html.Div([# submit dates to mask by button
            html.Button(id='submit-data',children='Submit date range selection.')
        ],style={"margin-top": "10px",'margin-bottom':'10px'}),
        html.Div(id='mask-range-output'), # output that file has been masked
        html.Div(id='df-storage',style={'display': 'none'}) # hidden div to store date-adjusted df
    ],className="pretty_container twelve columns"),

    # select the parameters, analysis, and bounds
    html.Div([
        html.H4('Analysis and Parameter Selection'),
        # parameters
        html.H6('Select parameter to analyze:'),
        html.Div([
            dcc.Dropdown(
                id='parameter-dropdown',
                options=[{'label': 'Temperature (Degrees Fahrenheit)', 'value':'Temp'},
                         {'label': 'Relative Humidity (%)','value': 'RH'},
                         {'label': 'Dew Point (Degrees Fahrenheit)', 'value': 'DP'}],
                value = 'Temp'
            )
        ],className="four columns"),
        # analysis
        html.Div([
            html.H6('Select the type of analysis to perform on above selected parameter. "Bounds" examines the'
                    ' minimum and maximum of the parameter and "Swing" examines the swing (i.e. the difference'
                    ' between the maximum and minimum value of the parameter over a 24 hour period.'),
        ],className='twelve columns'),
        html.Div([
            dcc.Dropdown(
                id='analysis-dropdown',
                options=[{'label': 'Bounds Analysis', 'value': 'BoundsAnalysis'},
                         {'label': 'Swing Analysis', 'value': 'SwingAnalysis'}],
                value = 'BoundsAnalysis'
            ),
        ],className="three columns"),
        # bounds
        html.Div([
            html.H6('Enter minimum and maximum bounds on the parameter selected above:',
                    id='bounds-text'),
            html.H6('Enter maximum permitted swing for the parameter selected above:',id='swing-text'),
        ],className='twelve columns'),
        # minimum input
        dcc.Input(
            id='input_min',
            type='number',
            placeholder= 'Enter minimum value...'
        ),
        # maximum input
        dcc.Input(
            id='input_max',
            type='number',
            placeholder= 'Enter maximum value...'
        ),
        # analyze button
        html.H6('Click submit to analyze the data file for the selected date range, parameter, and analyses above:'),
        html.Button(id='submit-button', children='Submit'),
    ], className="pretty_container twelve columns"),

    # outputs
    html.Div([
        html.H4('Output:'),
        html.Div(id='output-state'), # text
    ],className='pretty_container twelve columns'),
    # times series
    html.Div([
        html.H4('Time Series Graph'),
        dcc.Graph(id='Mygraph'),
    ],className='pretty_container twelve columns'),
    # contour plots
    html.Div([
        html.H4('Contour Plots'),
        html.Div([
            html.Div([
                dcc.Graph(id='contour-min')
            ],className = "six columns"),
            html.Div([
                dcc.Graph(id='contour-max'),
            ],className = "six columns"),
        ],className="row flex-display"),
    ],className='pretty_container twelve columns')
])

# FUNCTIONS_____________________________________________________________________________________________________________
# Note: This function is very specific to Winterthur and their .pm2 files
# creates dataframe out of .pm2 file
def parse_data(contents, startDate, endDate, monthsArray):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_table(io.BytesIO(decoded), skiprows=[0, 1, 3]) # skiprows is based on Winterthur file format
    df['DATE AND TIME GMT'] = pd.to_datetime(df['DATE AND TIME GMT']) # set date and time column as datetime type
    # rename columns
    df.columns = ['Date and Time in GMT', 'Temperature (Degrees Fahrenheit)', 'Relative Humidity (%)']

    # select the entered date range, from startDate to endDate
    maskRange = (df['Date and Time in GMT'] > startDate) & (df['Date and Time in GMT'] <= endDate)
    df = df.loc[maskRange]

    # if any specific months are selected, get rid of other months
    if monthsArray != []:
        df['month'] = df['Date and Time in GMT'].map(lambda x: x.strftime('%m'))  # pulls out month from data column
        df['month'] = pd.to_numeric(df['month'])  # recast month column as ints, not objects
        df = df[df['month'].isin(monthsArray)]

    return df

# if parameter selected is dew point, perform this function on the df to add a DP column
def add_DP_column(df):
    # convert F to C:
    temp = ((df['Temperature (Degrees Fahrenheit)'] - 32) * (5 / 9))
    RH = df['Relative Humidity (%)']
    # because converted to C, convert back to F at end of eq
    df['Dew Point'] =  ((((RH/100)**(1/8))*(112 + 0.9*temp)+0.1*temp - 112) * (9 / 5)) + 32
    return df

# perform swing analysis
def swing_analysis(df, swingInt,columnName): # columnName is a 'string'
    numEntries = len(df[columnName]) # length of data frame for rh
    pointsInDay = 24 * 60 / 15  # constant; number data points separated in 15 minute increments = 96 points
    lastValue = int(numEntries - pointsInDay - 1)     # calculate last "day", last possible complete 24 hour period

    # initialize blank rhSwing storage array
    swingArray = np.zeros(numEntries)  # could also be a new column in dataframe

    # for the number of possible 24-hour-long periods in the data set, loop; will be zero for end values
    for k in range(0, lastValue):
        jEnd = int(k + pointsInDay)
        # find maximum and minimum value over a one day (24 hour) period
        maxRH = max(df[columnName][k:jEnd])
        minRH = min(df[columnName][k:jEnd])
        # determine swing over 24 hour period and store in array
        swingArray[k] = maxRH - minRH
    df['swing'] = swingArray

    # if swing is greater than permitted, note how many times it is
    sum = 0
    for i in range(0, numEntries):
        if swingArray[i] >= swingInt:
            sum = sum + 1
    # sum = number of times RH Swing is out of bounds
    return swingArray, sum, lastValue, df

## CALLBACKS_____________________________________________________________________________________________________________
# displays name of file uploaded
@app.callback(Output('output-data-upload', 'children'),
              [Input('upload-data', 'filename')])
def update_output(filename):
    if filename is not None:
        children = 'You have selected the following file: {}'.format(filename)
        div = html.Div([html.H6(children=children, style={'color': '#4dbfff'})]) # changes text color to blue
        return div

# create df based on input date selection
@app.callback([Output('df-storage','children'),
              Output('mask-range-output','children')],
              [Input('submit-data','n_clicks')],
              [State('upload-data','contents'),
              State('upload-data', 'filename'),
              # start date
              State('startDateYear', 'value'),  # input
              State('startDateMonth', 'value'),  # dropdown, '1', '2', etc. for Jan, Feb, etc.
              State('start-day-dropdown', 'value'),  # dropdown, values come as string, corresponding to options
              State('start-hour-dropdown', 'value'),  # dropdown
              State('start-minute-dropdown', 'value'),  # dropdown
              # end date
              State('endDateYear', 'value'),  # input
              State('endDateMonth', 'value'),  # dropdown, '1', '2', etc. for Jan, Feb, etc.
              State('end-day-dropdown', 'value'),  # dropdown, values come as string, corresponding to options
              State('end-hour-dropdown', 'value'),  # dropdown
              State('end-minute-dropdown', 'value'),  # dropdown
              # dropdowns
              State('monthsToAnalyze','value')])
def upload_files(n_clicks, contents, filename, startYr, startMonth, startDay, startHr, startMin, endYr,
                               endMonth, endDay, endHr, endMin, monthsArray):
    if n_clicks is None:
        raise PreventUpdate
    else:
        # make dates into datetime format
        startDate = dt(startYr, startMonth, startDay, startHr, startMin)
        endDate = dt(endYr, endMonth, endDay, endHr, endMin)
        df = parse_data(contents, startDate, endDate, monthsArray)
        first = df['Date and Time in GMT'].iloc[0]
        last = df['Date and Time in GMT'].iloc[-1]

        children = 'You selected to look at the data between {} and {} (in GMT) for the months selected. For {}, ' \
                   'the date range is now {} to {} (GMT) based on the available data in the file (since some files ' \
                   'will not have data for all dates entered).'.format(startDate,endDate, filename, first, last)
        div = html.Div([html.H6(children=children, style={'color': '#4dbfff'})])
        return df.to_json(date_format='iso', orient='split'), div


# updates graph & analysis based on inputs
@app.callback([Output('Mygraph', 'figure'),
               Output('output-state','children'),
               Output('contour-min', 'figure'),
               Output('contour-max', 'figure')],
            [Input('submit-button','n_clicks')],
            [State('upload-data','filename'),
            State('df-storage','children'),
            State('parameter-dropdown','value'),
            State('analysis-dropdown','value'),
            State('input_min','value'),
            State('input_max','value')])
def update_graph_and_analysis(n_clicks, filename, df_storage, parameter, analysis, inputMin, inputMax):
    if n_clicks is None:
        figure = {'data': [{'x': [0], 'y': [0], 'name': 'N/A'}, ], 'layout':
            {'title': 'No data uploaded yet'}}
        return figure, dash.no_update, figure, figure
    else:
        df = pd.read_json(df_storage, orient='split')
        df['Date and Time in GMT'] = pd.to_datetime(df['Date and Time in GMT'])

        # assign column name according to parameter
        if parameter == 'DP':
            df = add_DP_column(df)
            columnName = 'Dew Point'
        elif parameter == 'Temp':
            columnName = 'Temperature (Degrees Fahrenheit)'
        else:
            columnName = 'Relative Humidity (%)'

        # pull out year and month
        df['year'] = pd.DatetimeIndex(df['Date and Time in GMT']).year
        # make arrays of years and months (just unique values)
        yearsArray = np.unique(df['year'])
        monthsArray = np.unique(df['month'])
        # create storage arrays
        storageMin = np.zeros([len(monthsArray), len(yearsArray)])
        storageMax = np.zeros([len(monthsArray), len(yearsArray)])

        if analysis == 'BoundsAnalysis':
            # determine max and min
            maxValueB = round(max(df[columnName]),2)
            minValueB = round(min(df[columnName]),2)
            # determine how often the data goes out of bounds
            # too low:
            numLow = np.sum(df[columnName] <= inputMin)
            numEntries = len(df[columnName])
            percentLow = round((numLow / numEntries) * 100,2)
            # too high:
            numHigh = np.sum(df[columnName] >= inputMax)
            numEntries = len(df[columnName])
            percentHigh = round((numHigh / numEntries) * 100,2)
            # out of bounds in general:
            percentOutOfBounds = round(percentLow + percentHigh,2)
            # value to return to text output:
            children = u''' The maximum value of {} is {} and the minimum value is {}.
            {} was less than the desired minimum {}% of the time.
            {} was greater than the desired maximum {}% of the time.
            Overall, {} was out of the desired bounds {}% of the time.
            '''.format(columnName, maxValueB,minValueB, columnName, percentLow, columnName, percentHigh, columnName,
                       percentOutOfBounds)

            # Add bound lines to time series graph
            df['Lower Bound'] = inputMin
            df['Upper Bound'] = inputMax

            # wrap title text
            title1 = columnName + ' Time Series for ' + filename
            split_text = textwrap.wrap(title1,width=100)
            title2 = '<br>'.join(split_text)
            # time series graph to return
            figure = {'data': [{'x': df['Date and Time in GMT'], 'y': df[columnName], 'name': filename},
                               {'x': df['Date and Time in GMT'], 'y': df['Lower Bound'],'name': 'Lower Bound'},
                               {'x': df['Date and Time in GMT'], 'y': df['Upper Bound'], 'name': 'Upper Bound'}
                              ],
                      'layout': {'title': title2,'xaxis':{'title':'Year'},'yaxis':{'title':columnName}}}

            # contour plots; prepare data
            for i in range(0, len(monthsArray)):
                for j in range(0, len(yearsArray)):
                    # creates boolean array of percentage out of bounds
                    totalPoints = np.sum((df['year'] == yearsArray[j]) & (df['month'] == monthsArray[i]))
                    outOfRangePoints = np.sum((df['year'] == yearsArray[j]) & (df['month'] == monthsArray[i]) &
                                              (df[columnName] <= inputMin))
                    outOfRangePoints2 = np.sum((df['year'] == yearsArray[j]) & (df['month'] == monthsArray[i]) &
                                              (df[columnName] >= inputMax))
                    storageMin[i, j] = (outOfRangePoints / totalPoints) * 100
                    storageMax[i, j] = (outOfRangePoints2 / totalPoints) * 100

            # "percent under bounds" contour plot
            figMin = go.Figure(data=
            go.Contour(
                z=storageMin,
                x=yearsArray,  # horizontal axis
                y=monthsArray, # vertical axis
                colorscale='GnBu'
            ))
            # control title length
            title3 = "Percentage of points where {} is below the desired minimum".format(columnName)
            split_text2 = textwrap.wrap(title3, width=50)
            title4 = '<br>'.join(split_text2)
            figMin.update_layout(
                title=title4,
                xaxis_title="Years",
                yaxis_title="Months"
            )

            # "percent over bounds" contour plot
            figMax = go.Figure(data=
            go.Contour(
                z=storageMax,
                x=yearsArray,  # horizontal axis
                y=monthsArray  # vertical axis
                ,
                colorscale='GnBu',
                contours=dict(
                    start=0,
                    end=np.max(storageMax),
                    size=2)
            ))
            # control title length
            title5 = "Percentage of points where {} is above the desired maximum".format(columnName)
            split_text3 = textwrap.wrap(title5, width=50)
            title6 = '<br>'.join(split_text3)
            figMax.update_layout(
                title=title6,
                xaxis_title="Years",
                yaxis_title="Months"
            )
            div = html.Div([html.H6(children=children)])
            return figure, div, figMin, figMax


        elif analysis == 'SwingAnalysis':
            # perform analysis
            swingArray, sum, lastValue, df = swing_analysis(df, inputMax, columnName)
            # max swing
            maxValueS = round(max(swingArray),2)
            # determine percent of time out of bounds
            numSwing = np.sum(swingArray >= inputMax)
            numEntries = len(swingArray)
            percentSwing = round(numSwing / numEntries * 100, 2)
            # text to output:
            children = u''' The maximum swing value for {} is {} and there were {} times that {} was out of the 
            permitted swing range of {}. The {} swing was out bounds {}% of the time.
            '''.format(columnName, maxValueS, sum, columnName, inputMax, columnName, percentSwing)

            # wrap title text
            title1 = columnName + ' Time Series for ' + filename
            split_text = textwrap.wrap(title1, width=100)
            title2 = '<br>'.join(split_text)
            # graph to return
            figure = {'data': [{'x': df['Date and Time in GMT'], 'y': df[columnName], 'name': filename}],
                'layout':{'title': title2,'xaxis':{'title':'Year'},'yaxis':{'title':columnName}}}

            # contour plot; prepare data
            for i in range(0, len(monthsArray)):
                for j in range(0, len(yearsArray)):
                    # creates boolean array of
                    totalPoints = np.sum((df['year'] == yearsArray[j]) & (df['month'] == monthsArray[i]))
                    outOfRangePoints = np.sum((df['year'] == yearsArray[j]) & (df['month'] == monthsArray[i]) &
                                              (df['swing'] >= inputMax))
                    storageMax[i, j] = (outOfRangePoints / totalPoints) * 100

            # create figure to send to interface
            figMax = go.Figure(data=
            go.Contour(
                z=storageMax,
                x=yearsArray,  # horizontal axis
                y=monthsArray,  # vertical axis
                colorscale='GnBu',
                contours=dict(
                    start=0,
                    end=np.max(storageMax),
                    size=2)
            ))
            # control title length
            title7 = "Percentage of points where {} swing is greater than the desired swing value".format(columnName)
            split_text4 = textwrap.wrap(title7, width=50)
            title8 = '<br>'.join(split_text4)
            figMax.update_layout(
                title=title8,
                xaxis_title="Years",
                yaxis_title="Months"
            )
            # only need one graph for swing, so adjust the left graph
            figMin = {'data': [{'x': [0], 'y': [0], 'name': 'N/A'}, ],
                      'layout': {'title': 'See graph at right for swing.'}}
            div = html.Div([html.H6(children=children)])
            return figure, div, figMin, figMax


# show/hide bound input boxes based on type of analysis being performed
@app.callback(Output(component_id='input_min', component_property='style'),
             [Input(component_id='analysis-dropdown', component_property='value')])
def show_hide_element(analysis):
    if analysis == 'SwingAnalysis':
        return {'display': 'none'}

# change suggested bound values depending on parameter and type of analysis
@app.callback([Output(component_id='input_min', component_property='value'),
               Output(component_id='input_max', component_property='value')],
              [Input(component_id='analysis-dropdown', component_property='value'),
              Input(component_id='parameter-dropdown', component_property= 'value')])
def change_value2(analysis, parameter):
    if analysis == 'SwingAnalysis':
        return 0, 10
    else:
        if parameter == 'Temp':
            return 63, 74
        elif parameter == 'RH':
            return 35, 57
        elif parameter == 'DP':
            return 37, 56

# change the text based on the analysis selected
@app.callback([Output('bounds-text','style'),
               Output('swing-text','style')],
              [Input('analysis-dropdown','value')])
def change_text(value):
    styleOn = {'display': 'inline-block'}
    styleOff = {'display': 'none'}
    if value == 'SwingAnalysis':
        return styleOff, styleOn
    else:
        return styleOn, styleOff

#_______________________________________________________________________________________________________________________
if __name__ == '__main__':
    app.run_server(debug = 'True') # runs app
