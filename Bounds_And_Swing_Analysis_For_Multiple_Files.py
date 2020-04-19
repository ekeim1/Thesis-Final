# import needed packages
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_floorplan
import dash_table
from dash.exceptions import PreventUpdate
from datetime import datetime as dt
import pandas as pd
import numpy as np
import base64
import io
import pickle

app = dash.Dash(__name__) # create app; also uses assets folder for stylesheets

# app layout
app.layout = html.Div([
    # title
    html.Div([
        html.H1(children='Winterthur Bounds and Swing Analysis Interface', style={'textAlign': 'center',"margin-bottom": "0px"}),
        html.H2(children='for Multiple Files', style={'textAlign': 'center',"margin-top": "0px"})
    ],style={"margin-bottom": "25px"}),

    # button to upload data files
    html.Div([
        html.H4(children='Upload data file(s) (.pm2 files supported):'),
        dcc.Upload(
            html.Button('Upload Data File(s)'),
            id='upload-data', style={'display': 'inline-block'},
            multiple=True # Allow multiple files to be uploaded
        ),
        # output selected data file filename
        html.Div(id='output-data-upload', style={'display': 'inline-block'}),
    ],className='pretty_container twelve columns'),

    # data range, parameter, analysis, and bounds selection
    html.Div([
        html.H4('Date Range, Parameter, and Analysis Selection'),
        # start date selection
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

        # end date selection
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
        # months to examine selection
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
        # parameter selection
        html.Div([html.H6('Select parameter to analyze.')],className='twelve columns'),
        html.Div([
            dcc.Dropdown(
                id='parameter-dropdown',
                options=[{'label': 'Temperature', 'value':'Temp'},{'label': 'Relative Humidity','value': 'RH'},
                         {'label': 'Dew Point', 'value': 'DP'}],
                value = 'Temp'
            )
        ],className="three columns"),
        # analysis selection
        html.Div([
            html.H6('Select the type of analysis to perform on above selected parameter. '
                    '"Bounds" examines the minimum and maximum of the parameter and "Swing" examines the swing (i.e. '
                    'the difference between the maximum and minimum value of the parameter over a 24 hour period.'),
        ],className='twelve columns'),
        html.Div([
            dcc.Dropdown(
                id='analysis-dropdown',
                options=[{'label': 'Bounds', 'value': 'BoundsAnalysis'}, {'label': 'Swing', 'value': 'SwingAnalysis'}],
                value = 'BoundsAnalysis'
            ),
        ],className="three columns"),
        # bounds selection
        html.Div([
            html.H6('Enter minimum and maximum bounds on the parameter selected above:',
                    id='bounds-text'),
            html.H6('Enter maximum permitted swing for the parameter selected above:', id='swing-text'),
        ], className='twelve columns'),
        # minimum input
        dcc.Input(
            id='input_min',
            type='number',
            value = 60,
            placeholder= 'Enter minimum value...'
        ),
        # maximum input
        dcc.Input(
            id='input_max',
            type='number',
            placeholder= 'Enter maximum value...'
        ),
        # analyze button
        html.H6('Click submit button below to analyze data with the selected above constraints. This will output'
                ' a table of the minimum value, maximum value, and percentage out of bounds for the selected '
                'parameter for each file.'),
        html.Button(id='submit-button', children='Submit'),
    ], className="pretty_container twelve columns"),

    # output text and table
    html.Div([
        html.H4('Output:'),
        html.Div(id='output-state'),
        html.Div(id='analysis-results',style={'display': 'none'}),
        html.Div(id='table'),
    ],className='pretty_container twelve columns'),

    # visualize on floorplan
    html.H1('Visualize'),
    html.Div([
        # send data to visualizer
        html.Div([
            html.H4('Visualization on Floorplan'),
            html.H6('Click "Send data to visualizer" below to send results from above to '
                    'the visualizer. The parameters will show up below in red.'),
            html.Button(id='room-names-button', children='Send data to visualizer'),
            html.Div(id='room-name-result'),  # tells you what factor you are using
        ],className='pretty_container five columns'),

        # upload image
        html.Div([
            html.H4('Upload Floorplan Image'),
            html.H6('Type the url of the Google Drawing containing your image and click the '
                    'button. Only Google Drawings and urls ending in .jpg, .png will work. To work with multiple images, put '
                    'them all in the same Google Drawing. Make sure your Google Drawing is published to the web, which can be '
                    'done by clicking "File", "Publish to the web", selecting the image size, and hitting "Publish".'
                    ' Copy the link given and paste it below. Make sure to unpublish the image if you do not want other to '
                    'access it when you are done using this application.'),
            dcc.Input(id='floorplan-image-input', value=''),
            html.Button(id='floorplan-upload-button', children='Upload floorplan image.'),
        ],className='pretty_container seven columns'),
    ],className='row flex-display'),

    #polygons
    html.Div([
        # explanations
        dcc.Markdown('''### **Polygons**'''),
        html.H6('Polygons are how rooms are labeled on the floorplan. Click on the polygon to associate it '
            'with a room, using the dropdown menu above the floorplan. "Menu" allows you to delete and duplicate a '
            'polygon. Room names will turn from red to green when they have been associated with a polygon. '
            'Polygons will appear grey until associated with a room.'),
        dcc.Markdown(''' ##### **To make new polygons:**'''),
        html.H6(
            'Double click to begin a polygon. Single click to make edge points of that polygon and then click the inital'
            ' starting point to close the polygon. The polygon will then appear.'),

        # upload polygons saved prior
        dcc.Markdown(''' ##### **To upload polygons saved from a prior session:**'''),
        html.H6('Enter the file path of your saved polgyons, for example: E:\saved_polygons.pickle, and then press the '
                'Submit button.'),
        dcc.Input(id='shapes-path', value='E:\saved_polygons.pickle'),
        html.Button(id='shapes-upload', children='Submit file path to upload saved polygons.'),
        html.Div(id='upload-shapes-output'),

        # save current polygons
        dcc.Markdown('''##### **To save polygons you have drawn and associated with room names:**'''),
        html.H6('Enter the path you wish to save the polygon data file to in the input box below. Click the button below to'
                ' save your polygons to your computer. The file location will output so that you can see where they were '
                'saved. Polygons will be saved in a .pickle file.'),
        dcc.Input(id='save-points-input', value='E:\saved_shapes'),
        html.Button(id='save-points', children='Click to save the polygons currently drawn, as well as the room names that '
                                               'have been associated with them.'),
        html.Div(id='save-points-output'),
    ],className='pretty_container twelve columns'),

    # floorplan coloring explanation
    html.Div([
        html.H6(id='bounds-explanation', children = 'For Bounds Analysis, yellow shading indicates a room was both over and'
                                                    ' under the desired bounds. Red shading indicates the room was only '
                                                    'over the desired bounds. Blue shading indicates the room was only '
                                                    'below the desired bounds. Green shading indicates the room was within '
                                                    'the desired bounds.'),
        html.H6(id='swing-explanation', children = 'For Swing Analysis, red shading indicates a swing over the maximum '
                                                   'desired swing in that room. Green indicates a swing within the desired '
                                                   'swing range.'),
        # dash floorplan component
        dash_floorplan.DashFloorPlan(
            id='dash-floorplan',
            width=1024,
            height=768,
            selection=None,
            shapes=[],
            update=False,
            # rooms
            data={},
            image=''
        )
    ],className='pretty_container twelve columns'),

])

# FUNCTIONS_____________________________________________________________________________________________________________
# this function is very specific to Winterthur and their .pm2 files
# creates dataframe of files
def parse_data(contents, startDate, endDate, monthsArray):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_table(io.BytesIO(decoded), skiprows=[0, 1, 3])
    # set date and time column as datetime type
    df['DATE AND TIME GMT'] = pd.to_datetime(df['DATE AND TIME GMT'])
    # rename columns
    df.columns = ['Date and Time in GMT', 'Temperature (Degrees Fahrenheit)', 'Relative Humidity (%)']
    # select the entered date range, from startDate to endDate
    maskRange = (df['Date and Time in GMT'] > startDate) & (df['Date and Time in GMT'] <= endDate)
    df = df.loc[maskRange]
    # if any specific months are selected, get rid of other months
    if monthsArray != []: # if any month is selected the array will not be all zeros
        df['month'] = df['Date and Time in GMT'].map(lambda x: x.strftime('%m'))  # pulls out month from data column
        df['month'] = pd.to_numeric(df['month'])  # recast month column as ints, not objects
        df = df[df['month'].isin(monthsArray)]
    return df

# add DP column to a dataframe that has T and RH
def add_DP_column(df):
    # convert F to C:
    temp = ((df['Temperature (Degrees Fahrenheit)'] - 32) * (5 / 9))
    RH = df['Relative Humidity (%)']
    # because converted to C, convert back to F at end of eq
    df['Dew Point'] =  ((((RH/100)**(1/8))*(112 + 0.9*temp)+0.1*temp - 112) * (9 / 5)) + 32
    return df

# swing analysis
def swing_analysis(df, swingInt,columnName): # columnName is a 'string'
    numEntries = len(df[columnName]) # length of data frame for rh
    pointsInDay = 24 * 60 / 15  # constant; number data points separated in 15 minute increments = 96 points
    lastValue = int(numEntries - pointsInDay - 1)     # calculate last "day", last possible complete 24 hour period

    # initialize blank Swing storage array
    swingArray = np.zeros(numEntries)  # could also be a new column in dataframe

    # for the number of possible 24hr periods in the data set, loop; will be zero for end values
    for k in range(0, lastValue):
        jEnd = int(k + pointsInDay)
        # find maximum and minimum value over a one day period
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
def update_output(list_of_names):
    if list_of_names is not None:
        children = 'The following selected files have been uploaded: {}'.format(list_of_names)
        div = html.Div([html.H6(children=children, style={'color': '#4dbfff'})])
        return div

# updates graph & analysis based on inputs
@app.callback([Output('output-state','children'),
               Output('analysis-results','children'),
               Output('table', 'children')],
            [Input('submit-button','n_clicks')],
            [State('upload-data', 'contents'),
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
            State('monthsToAnalyze','value'),
            State('parameter-dropdown','value'),
            State('analysis-dropdown','value'),
            State('input_min','value'),
            State('input_max','value')
            ])
def update_graph__and_analysis(n_clicks, list_contents, list_filenames, startYr, startMonth, startDay, startHr,
                               startMin, endYr, endMonth, endDay, endHr, endMin, monthsArray, parameter, analysis,
                               inputMin, inputMax):
    if n_clicks is None:
        raise PreventUpdate
    else:
        Dict={} # storage
        startDate = dt(startYr, startMonth, startDay, startHr, startMin)
        endDate = dt(endYr, endMonth, endDay, endHr, endMin)
        if parameter == 'DP':
            columnName = 'Dew Point'
        elif parameter == 'Temp':
            columnName = 'Temperature (Degrees Fahrenheit)'
        else:
            columnName = 'Relative Humidity (%)'

        if analysis == 'BoundsAnalysis':
            i = 0 # counter
            storage = pd.DataFrame(columns=['Room Name','Minimum Value','Maximum Value',
                                            'Percent Out of Bounds Total (%)', 'Percent Over Upper Bound (%)',
                                            'Percent Under Lower Bound (%)'])
            for filename, contents in zip(list_filenames, list_contents):
                df = parse_data(contents, startDate, endDate, monthsArray)
                if parameter == 'DP':
                    df = add_DP_column(df)
                # determine max and min
                maxValueB = round(max(df[columnName]),2)
                minValueB = round(min(df[columnName]),2)
                # determine how often the data goes out of bounds
                # too low:
                numLow = np.sum(df[columnName] <= inputMin)
                numEntries = len(df[columnName])
                percentLow = round(numLow / numEntries,2)
                # too high:
                numHigh = np.sum(df[columnName] >= inputMax)
                numEntries = len(df[columnName])
                percentHigh = round(numHigh / numEntries,2)
                # out of bounds in general:
                percentOutOfBounds = round(percentLow + percentHigh,2)

                #floorplan calcs:
                if (maxValueB > inputMax and minValueB < inputMin):
                    # color is yellow = 0.5
                    Dict[filename] = 0.5 # percentOutOfBounds
                elif maxValueB > inputMax:
                    # color red = 0.2
                    Dict[filename] = 0.2 # percentHigh
                elif minValueB < inputMin:
                    # color blue = 0.9
                    Dict[filename] = 0.9# percentLow
                else: #within bounds
                    Dict[filename] = 0.7 # color green = 0.7
                # for table:
                storage.loc[i, ['Room Name']] = filename
                storage.loc[i, ['Minimum Value']] = minValueB
                storage.loc[i, ['Maximum Value']] = maxValueB
                storage.loc[i, ['Percent Out of Bounds Total (%)']] = percentOutOfBounds * 100
                storage.loc[i, ['Percent Over Upper Bound (%)']] = percentLow *100
                storage.loc[i, ['Percent Under Lower Bound (%)']] = percentHigh *100
                i=i+1 # increment count
            children = 'You selected to look at the data between {} and {} (in GMT) for the months selected. ' \
                       'You have selected to perform a Bounds Analysis for {} where the minimum bound was {} and ' \
                       'the maximum bound was {}.'.format(startDate, endDate, columnName, inputMin, inputMax)
            table = dash_table.DataTable(
                columns=[{"name": i, "id": i} for i in storage.columns],
                data=storage.to_dict('records'))
            div = html.Div([html.H6(children=children)])
            return div, Dict, table

        elif analysis == 'SwingAnalysis':
            i = 0 # counter
            storage = pd.DataFrame(columns=['Room Name','Maximum Swing','Percent of Data with Swing Greater '
                                                                        'than Desired Swing (%)'])
            for filename, contents in zip(list_filenames, list_contents):
                df = parse_data(contents, startDate, endDate, monthsArray)
                if parameter == 'DP':
                    df = add_DP_column(df)
                # perform analysis
                swingArray, sum, lastValue, df = swing_analysis(df, inputMax, columnName) #sum is number of times out of bounds
                maxValueS = round(max(swingArray),2) # max swing value
                # determine percent of time out of bounds
                numSwing = np.sum(swingArray >= inputMax)
                numEntries = len(swingArray)
                percentSwing = round(numSwing / numEntries, 2)

                # for floorplan:
                if maxValueS > inputMax:
                    # color is red = 0.2
                    Dict[filename]= 0.2 #percentSwing # opacity
                else:
                    Dict[filename]=0.7 # color is green = 0.7
                storage.loc[i, ['Room Name']] = filename
                storage.loc[i, ['Maximum Swing']] = maxValueS
                storage.loc[i, ['Percent of Data with Swing Greater than Desired Swing (%)']] = percentSwing * 100
                i = i + 1  # increment count
            children = 'You selected to look at the data between {} and {} (in GMT) for the months selected. ' \
                       'You have selected to perform a Swing Analysis for {} where the desired maximum swing' \
                       ' was {}.'.format(startDate, endDate, columnName, inputMax)
            table = dash_table.DataTable(
                columns=[{"name": i, "id": i} for i in storage.columns],
                data=storage.to_dict('records'))
            div = html.Div([html.H6(children=children)])
            return div, Dict, table


# show/hide bound input boxes based on type of analysis being performed
@app.callback(Output(component_id='input_min', component_property='style'),
             [Input(component_id='analysis-dropdown', component_property='value')])
def show_hide_element(analysis):
    if analysis == 'SwingAnalysis':
        return {'display': 'none'}

# change suggested bound values depending on parameter and type of analysis
@app.callback([Output(component_id='input_min', component_property='value'),
               Output(component_id='input_max', component_property='value'),
               Output('bounds-explanation','style'),
               Output('swing-explanation', 'style')],
              [Input(component_id='analysis-dropdown', component_property='value'),
              Input(component_id='parameter-dropdown', component_property= 'value')])
def change_value2(analysis, parameter):
    style1 = {'display': 'none'}
    style2 = {'display':'block'}
    if analysis == 'SwingAnalysis':
        return 0, 10, style1, style2
    else:
        if parameter == 'Temp':
            return 63, 74, style2, style1
        elif parameter == 'RH':
            return 35, 57, style2, style1
        elif parameter == 'DP':
            return 37, 56, style2, style1


# update floorplan to have room names of data files uploaded
# filters data based on the radio button picked, either temp or rh correlation comparison
# colors are based on the number given as a value of the key in the data dictionary
# i.e. 'room 2': 0.8 --> 0.8 is helps determine the color
@app.callback([Output('dash-floorplan','data'),
               Output('room-name-result','children')],
              [Input('room-names-button','n_clicks')],
              [State('analysis-results', 'children')]) #factors
def send_data_to_floorplan(n_clicks, results):
    if n_clicks is None:
        raise PreventUpdate
    else:
        children = 'Data has been sent to the visualizer.'
        div = html.Div([html.H6(children=children, style={'color': '#4dbfff'})])
        return results, div


# upload polygons from prior session; upload image for floorplan
@app.callback([Output('upload-shapes-output', 'children'),
               Output('dash-floorplan', 'shapes'),
               Output('dash-floorplan', 'image'),
               Output('dash-floorplan', 'update')],
              [Input('shapes-upload', 'n_clicks'),
               Input('floorplan-upload-button', 'n_clicks')],
              [State('shapes-path', 'value'),
               State('floorplan-image-input', 'value')])
def save_shapes(n_clicks, n_clicks2, path, value):  # filename, contents):
    # figure out which button was clicked
    ctx = dash.callback_context
    if ctx.triggered[0]['value'] is None:
        raise PreventUpdate
    else:
        button_clicked = ctx.triggered[0]['prop_id'].split('.')[0]

        # shapes uploaded callback
        if button_clicked == 'shapes-upload':
            if n_clicks is None:
                raise PreventUpdate
            else:
                uploaded_shapes = pickle.load(open(path, "rb"))  # read in pickle file
                children = 'Polygons have been uploaded.'
                div = html.Div([html.H6(children=children, style={'color': '#4dbfff'})])
                return div, uploaded_shapes, dash.no_update, True  # dash.no_update if don't want to return anything


        else: # if button_clicked == 'floorplan-upload-button':
            if n_clicks2 is None:
                raise PreventUpdate
            else:
                image = value + ''  # to ensure string
                return dash.no_update, dash.no_update, image, True


# save polygons to use again later
@app.callback(Output('save-points-output','children'),
              [Input('save-points','n_clicks')],
              [State('save-points-input','value'),
               State('dash-floorplan','shapes')])
def save_points(n_clicks, value, shapes):
    if n_clicks is None:
        raise PreventUpdate
    else:
        path = value + '.pickle'  # add .pickle to name
        pickle.dump(shapes, open(path, "wb")) # save as pickle file
        children = 'File has been saved at the following location: ' + path
        div = html.Div([html.H6(children=children, style={'color': '#4dbfff'})])
        return div


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

# ______________________________________________________________________________________________________________________
if __name__ == '__main__':
    app.run_server(debug = 'True') # runs app
