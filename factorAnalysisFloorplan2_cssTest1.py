# import needed packages
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_floorplan
from dash.exceptions import PreventUpdate
import pandas as pd
import numpy as np
from factor_analyzer import FactorAnalyzer
from factor_analyzer.factor_analyzer import calculate_bartlett_sphericity
from factor_analyzer.factor_analyzer import calculate_kmo
import plotly.graph_objects as go
import pickle
import base64
import io

app = dash.Dash(__name__) # make app

# read in colorbar image (for color scale on floorplan)
encoded_image = base64.b64encode(open('colorbarSpectralhorz.png', 'rb').read())
image_src = 'data:image/png;base64,{}'.format(encoded_image.decode())

# APP LAYOUT____________________________________________________________________________________________________________
app.layout = html.Div([
    # title
    html.Div([
        html.H1(children='Winterthur Factor Analysis Interface', style={'textAlign': 'center'})
    ],style={"margin-bottom": "25px"}),

    # upload files
    html.Div([
        html.H3('Upload Data'),
        html.H6(children='Please select whether you have a dataset saved from a prior session to upload (.pickle or .csv '
                         'format):'),
        # pick whether need to upload new data or from prior session
        dcc.RadioItems(
            id='radio-buttons',
            options=[
                {'label': 'No, I need to upload separate .pm2 files and have them made into a dataset.',
                 'value': 'no-pickle'},
                {'label': 'Yes, I have a .pickle file or .csv to upload from a prior session.', 'value': 'yes-pickle'}
            ],
            value='no-pickle'
        ),

        # upload pm2s
        html.H6(id='pm2-label',
                children='Upload all .pm2 files you wish to use during factor analysis.'),
        dcc.Upload(
            html.Button('Upload .pm2 files'),
            id='many-pm2-upload', style={'display': 'inline-block'}, multiple=True
        ),
        html.Div(id='output-pm2-data-upload', style={'display': 'inline-block'}),
        html.Div(id='df-pm2-storage', style={'display': 'none'}),
        # save pm2 files text
        html.H6('If you wish to save the files uploaded above as a dataset for use in a later session, enter the file'
                ' path you wish to save the file to in the input box below. The file can be saved as a .pickle file or a'
                ' .csv file. Pickle files load more quickly in a later session, while csv files can be opened in a '
                'spreadsheet to ensure the dataset made is as desired.',
                 id = 'save-file-text',),
        dcc.Input(id='save-file-input', value='E:\saved_pickle_file', debounce=True),
        html.Button(id='save-pickle-file', children='Save to computer as .pickle file.'),
        html.Div(id='pickle-output'),
        html.Button(id='save-csv-file', children='Save to computer as .csv file.'),
        html.Div(id='csv-output'),

        # upload .csv or .pickle from prior session
        html.H6(id='pickle-label', children='Upload dataset from a prior session (.csv or .pickle):'),
        dcc.Upload(
            html.Button('Upload .pickle or .csv file'),
            id='upload-pickle-data', style={'display': 'inline-block'},
        ),

        # output selected data file filename
        html.Div(id='output-pickle-data-upload', style={'display': 'inline-block'}),
        # Hidden div inside the app that stores the created dataframe
        html.Div(id='df-storage', style={'display': 'none'}),

        # save .pickle as .csv or vice versa
        html.H6('If you wish to save your uploaded file as another type, enter the file path you wish to save the file '
                 'to in the input box below. '
                 'Click the "save as .pickle" button to save a .pickle of your uploaded .csv file. '
                 'Click the  "save as .csv" button to save a .csv copy of your uploaded pickle file. '
                 'Pickle files load more quickly in a later session, while csv files can be opened in a '
                 'spreadsheet to ensure the dataset made is as desired.',
                 id='save-file-text2'),
        dcc.Input(id='save-file-input2', value='E:\saved_pickle_file', debounce=True),
        html.Button(id='save-pickle-file2', children='Save .csv file as .pickle file.'),
        html.Div(id='pickle-output2'),
        html.Button(id='save-csv-file2', children='Save .pickle file as .csv file.'),
        html.Div(id='csv-output2')
    ],className='pretty_container twelve columns'),

    # check that factor analysis is ok; three tests
    html.H3('Ensure the dataset is suitable for factor analysis:', style={'textAlign': 'center'}),
    html.Div([
        # bartlett test
        html.Div([
            html.H4(children='Bartlett Test'),
            html.H6(children='The p-value should be less than or equal to 0.05 in order to run factor analysis.'),
            html.Button(id='bartlett-button', children='Run Bartlett Test'),
            html.H6(children='p-value:'),
            html.H6(id='Bartlett-output-p'),
            html.H6(id='Bartlett-descrip'),
        ], className="pretty_container six columns"),

        # KMO test
        html.Div([
            html.H4(children='Kaiser-Meyer-Olkin Test'),
            html.H6(children='The KMO value should be greater than or equal to 0.6 in order to run factor analysis.'),
            html.Button(id='kmo-button', children='Run KMO Test'),
            html.H6(children='KMO value:'),
            html.H6(id='kmo-output'),
            html.H6(id='kmo-descrip'),
        ],className="pretty_container six columns")
    ],className="row flex-display"),

    # eigenvalues
    html.Div([
        html.H4(children='Eigenvalues'),
        html.H6(
            'Click the button below to show eigenvalues. Use the maximum number of factors and the scree plot to '
            'determine the number of factors to use for analysis. Look for a change in slope for the scree plot, for'
            ' eigenvalues greater than 1.'),
        html.Button(id='eigen-button', children='Click to analyze eigenvalues'),
        html.H6(children='Maximum number of meaningful factors:'),
        html.H6(id='eigen-output2'),
        dcc.Graph(id='scree-plot'), # scree plot
    ],className='pretty_container twelve columns'),

    # select number of factors and run factor analysis
    html.Div([
        html.H3('Analyze:'),
        html.H6(children='Select the number of factors desired to be analyzed, based on the above results.'),
        dcc.RadioItems(id='numFactors'),
        # button to run factor analysis once you have run all of the above and confirmed ok to run FA
        html.Button(id='FA-button', children='Run Factor Analysis using number of factors entered above.'),

        # display text results of FA upon clicking above button
        html.H6('Factors and Parameters:'),
        html.Div([dcc.Textarea(id='FA-results',style={'width': '50%', 'height': 200})],className='twelve columns'),
        html.H6('Proportional Variance by factor:'),
        html.Div([dcc.Textarea(id='var-results',style={'width': '50%', 'height': 100})],className='twelve columns'),
        html.H6('Total Variance explained by all factors:'),
        html.Div([dcc.Textarea(id='total-var', style={'width': '50%', 'height': 50})], className='twelve columns'),
        html.Div(id='FA-results-storage', style={'display': 'none'}),  # hidden div
    ],className='pretty_container twelve columns'),

    # bar graph
    html.Div([
        html.H3('Bar Graph'),
        html.H6('Select the factor you wish to graph and click "Make Bar Graph".'),
        dcc.RadioItems(id='bar-radios'),
        html.Button(id='bar-graph-button', children='Make Bar Graph.'),
        dcc.Graph(id='bar-graph'),
    ],className='pretty_container twelve columns'),

    # visualization
    html.H1('Visualize'),
    html.Div([
        # send data to visualizer
        html.Div([
            html.H4('Send data to floorplan'),
            html.H6('Select factor to visualize and then click "Send data to visualizer" below to send results from above to '
                    'the floorplan visualizer.'),
            dcc.RadioItems(id='floorplan-radios'),
            html.Button(id='room-names-button', children='Send data to visualizer'),  # 'Click to send correlation data to visualizer.'),
            html.Div(id='room-name-result'), # tells you what factor you are using
        ],className="pretty_container five columns"),

        # upload image
        html.Div([
            html.H4('Upload floorplan image'),
            html.H6('Type the url of the Google Drawing containing your image and click the '
                    'button. Only Google Drawings and urls ending in .jpg, .png will work. To work with multiple images, put '
                    'them all in the same Google Drawing. Make sure your Google Drawing is published to the web, which can be '
                    'done by clicking "File", "Publish to the web", selecting the image size, and hitting "Publish".'
                    ' Copy the link given and paste it below. Make sure to unpublish the image if you do not want other to '
                    'access it when you are done using this application.'),
            dcc.Input(id='floorplan-image-input', value='https://docs.google.com/drawings/d/e/2PACX-1vQ-kcZ0xUxaCPD_lEtxthJPBBGWNOnfj3HUhTVh7h2rmDEfY63kjd7y8m2g0eHWux5pAmtTbg7dJK52/pub?w=1368&h=864'),
            html.Button(id='floorplan-upload-button', children='Upload floorplan image'),
        ],className='pretty_container seven columns'),
    ],className='row flex-display'),

    # polygons
    html.Div([
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
        html.Button(id='shapes-upload', children='Submit file path to upload saved polygons'),
        html.Div(id='upload-shapes-output'),
        # save current polygons
        dcc.Markdown('''##### **To save polygons currently on floorplan and associated room names:**'''),
        html.H6('Enter the path you wish to save the polygon data file to in the input box below. Click the button below to'
                ' save your polygons to your computer. The file location will output so that you can see where they were '
                'saved. Polygons will be saved in a .pickle file.'),
        dcc.Input(id='save-points-input', value='E:\saved_shapes'),
        html.Button(id='save-points', children='Save current polygons'),
        html.Div(id='save-points-output'),
    ],className='pretty_container twelve columns'),

    # dash floorplan component
    html.Div([
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
        ),
        html.Div([html.Img(id='colorbar', src=image_src, style={'width': 1000, 'height': 100})])
    ],className='pretty_container twelve columns'),

])


# FUNCTIONS_____________________________________________________________________________________________________________
# make .pm2 file into a dataframe (specific to Winterthur)
def make_df_pm2(filename, contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_table(io.BytesIO(decoded), skiprows=[0, 1, 3])
    # set date and time column as datetime type
    df['DATE AND TIME GMT'] = pd.to_datetime(df['DATE AND TIME GMT'])
    # rename columns
    df.columns = ['Date and Time in GMT', 'Temperature (Degrees Fahrenheit)', 'Relative Humidity (%)']
    df = df.set_index('Date and Time in GMT')
    # resample data to fill in any gaps and to ensure same time interval
    upsampledTemp = df['Temperature (Degrees Fahrenheit)'].resample('15min').mean()
    interpolatedTemp = upsampledTemp.interpolate(method='linear')
    upsampledRH = df['Relative Humidity (%)'].resample('15min').mean()
    interpolatedRH = upsampledRH.interpolate(method='linear')
    # create new dataframe with the resampled values
    frame = {'Temp_{}'.format(filename): interpolatedTemp,
             'RH_{}'.format(filename): interpolatedRH}
    result = pd.DataFrame(frame)
    return result


# create dataframe from .pickle or .csv file
def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            df['Date and Time in GMT'] = df['Date and Time in GMT'].astype('datetime64[ns]')
            df = df.set_index('Date and Time in GMT')
            return df
        elif 'pickle' in filename:
            df = pd.read_pickle(io.BytesIO(decoded))
            return df
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file. Please upload a .pickle or .csv file.'
        ])


# CALLBACKS_____________________________________________________________________________________________________________
# pickle or no pickle radio; hides upload .pm2 files if have .pickle file from prior session
@app.callback([Output('upload-pickle-data', 'style'),
               Output('output-pickle-data-upload', 'style'),
               Output('pickle-label', 'style'),
               Output('many-pm2-upload', 'style'),
               Output('output-pm2-data-upload', 'style'),
               Output('pm2-label', 'style'),
               Output('csv-output','style'),
               Output('save-csv-file','style'),
               Output('pickle-output', 'style'),
               Output('save-pickle-file', 'style'),
               Output('save-file-text','style'),
               Output('save-file-input','style'),
               Output('csv-output2', 'style'),
               Output('save-csv-file2', 'style'),
               Output('pickle-output2', 'style'),
               Output('save-pickle-file2', 'style'),
               Output('save-file-text2','style'),
               Output('save-file-input2','style')],
              [Input('radio-buttons', 'value')])
def hide_components(value):
    styleOn = {'display': 'inline-block'}
    styleOff = {'display': 'none'}
    if value == 'yes-pickle':
        return styleOn, styleOn, styleOn, styleOff, styleOff, styleOff, styleOff, styleOff, styleOff, styleOff, \
               styleOff, styleOff, styleOn, styleOn, styleOn, styleOn, styleOn, styleOn
    elif value == 'no-pickle':
        return styleOff, styleOff, styleOff, styleOn, styleOn, styleOn, styleOn, styleOn, styleOn, styleOn, styleOn,\
               styleOn, styleOff, styleOff, styleOff, styleOff, styleOff, styleOff


# uploads .pm2 files and makes dataframe out of them
@app.callback([Output('output-pm2-data-upload', 'children'),
               Output('df-pm2-storage', 'children')],
              [Input('many-pm2-upload', 'filename')],
              [State('many-pm2-upload', 'contents')])
def update_output(list_filenames, list_contents):
    if list_filenames is not None:
        result_df = pd.DataFrame()  # empty
        # loop through each file
        for filename, contents in zip(list_filenames, list_contents):
            df = make_df_pm2(filename, contents)
            # store values in overall storage dataframe, result_df
            result_df['Temp_{}'.format(filename)] = df['Temp_{}'.format(filename)]
            result_df['RH_{}'.format(filename)] = df['RH_{}'.format(filename)]
        # drop NaN values (will drop any row with NaN values
        result_df.dropna(inplace=True)
        ret = 'Files have been uploaded.'
        div = html.Div([html.H6(children=ret,style= {'color': '#4dbfff'})])
        return div, result_df.to_json(date_format='iso', orient='split')


# uploads .pickle or .csv file of already made dataframe
@app.callback([Output('output-pickle-data-upload', 'children'),
               Output('df-storage', 'children')],
              [Input('upload-pickle-data', 'filename')],
              [State('upload-pickle-data', 'contents')])
def update_output(filename, contents):
    if contents is not None:
        # print out name of file selected on interface
        children = 'You selected the following file: ', filename
        # build dataframe to store in a hidden div in json form so that all callbacks can reference it
        new_df = parse_contents(contents, filename)
        div = html.Div([html.H6(children=children, style={'color': '#4dbfff'})])
        return div, new_df.to_json(date_format='iso', orient='split')


# save pickle as csv
@app.callback(Output('csv-output2', 'children'),
              [Input('save-csv-file2', 'n_clicks')],
              [State('save-file-input', 'value'),
               State('df-storage', 'children')])
def save_files(n_clicks, value, df):
    if n_clicks is None:
        raise PreventUpdate
    else:
        path = value + '.csv'  # add .pickle to name
        dff = pd.read_json(df, orient='split')
        dff.to_csv(path)  # make into pickle file
        children = 'File has been saved at the following location: ' + path
        div = html.Div([html.H6(children=children, style={'color': '#4dbfff'})])
        return div


# save csv as pickle
@app.callback(Output('pickle-output2', 'children'),
              [Input('save-pickle-file2', 'n_clicks')],
              [State('save-file-input', 'value'),
               State('df-storage', 'children')])
def save_files(n_clicks, value, df):
    if n_clicks is None:
        raise PreventUpdate
    else:
        path = value + '.pickle'  # add .pickle to name
        dff = pd.read_json(df, orient='split')
        dff.to_pickle(path)  # make into pickle file
        children = 'File has been saved at the following location: ' + path
        div = html.Div([html.H6(children=children, style={'color': '#4dbfff'})])
        return div


# save .pm2 dataframe as csv
@app.callback(Output('csv-output', 'children'),
              [Input('save-csv-file', 'n_clicks')],
              [State('save-file-input', 'value'),
               State('df-pm2-storage', 'children')])
def save_files(n_clicks, value, df):
    if n_clicks is None:
        raise PreventUpdate
    else:
        path = value + '.csv'  # add .pickle to name
        dff = pd.read_json(df, orient='split')
        dff.to_csv(path)  # make into pickle file
        children = 'File has been saved at the following location: ' + path
        div = html.Div([html.H6(children=children, style={'color': '#4dbfff'})])
        return div


# save .pm2 dataframe as pickle
@app.callback(Output('pickle-output', 'children'),
              [Input('save-pickle-file', 'n_clicks')],
              [State('save-file-input', 'value'),
               State('df-pm2-storage', 'children')])
def save_files(n_clicks, value, df):
    if n_clicks is None:
        raise PreventUpdate
    else:
        path = value + '.pickle'  # add .pickle to name
        dff = pd.read_json(df, orient='split')
        dff.to_pickle(path)  # make into pickle file
        children = 'File has been saved at the following location: ' + path
        div = html.Div([html.H6(children=children, style={'color': '#4dbfff'})])
        return div


# bartlett test
@app.callback([Output('Bartlett-output-p', 'children'),
               Output('Bartlett-descrip','children')],
              [Input('bartlett-button', 'n_clicks')],
              [State('df-storage', 'children'),
               State('df-pm2-storage', 'children'),
               State('radio-buttons', 'value')])
def barlett_analysis(n_clicks, df1, df2, value):  # ,filename):
    if n_clicks is None:
        raise PreventUpdate
    else:
        if value == 'yes-pickle':
            dff = pd.read_json(df1, orient='split')
            chi_square_value, p_value = calculate_bartlett_sphericity(
                dff)  # so this needs to be a df created from the input files
            if p_value <= 0.05:
                children = 'p-value is significant. Factor analysis may proceed.'
                div = html.Div([html.H6(children=children, style={'color': '#4dbfff'})])
                return p_value, div
            else:
                children = 'p-value is not significant. Factor analysis should not proceed. The dataset should be ' \
                           'adjusted in order to run factor analysis.'
                div = html.Div([html.H6(children=children, style={'color': '#4dbfff'})])
                return p_value, div
        elif value == 'no-pickle':
            dff = pd.read_json(df2, orient='split')
            chi_square_value, p_value = calculate_bartlett_sphericity(
                dff)  # so this needs to be a df created from the input files
            if p_value <= 0.05:
                children = 'p-value is significant. Factor analysis may proceed.'
                div = html.Div([html.H6(children=children, style={'color': '#4dbfff'})])
                return p_value, div
            else:
                children = 'p-value is not significant. Factor analysis should not proceed. The dataset should be ' \
                           'adjusted in order to run factor analysis.'
                div = html.Div([html.H6(children=children, style={'color': '#4dbfff'})])
                return p_value, div


# kmo test
@app.callback([Output('kmo-output', 'children'),
               Output('kmo-descrip','children')],
              [Input('kmo-button', 'n_clicks')],
              [State('df-storage', 'children'),
               State('df-pm2-storage', 'children'),
               State('radio-buttons', 'value')])
def kmo_anlaysis(n_clicks, df1, df2, value):
    if n_clicks is None:
        raise PreventUpdate
    else:
        if value == 'yes-pickle':
            dff = pd.read_json(df1, orient='split')
            kmo_per_item, kmo_total = calculate_kmo(dff)
            if kmo_total >= 0.6:
                children = 'KMO-value is greater than 0.6. Factor analysis may proceed.'
                div = html.Div([html.H6(children=children, style={'color': '#4dbfff'})])
                return kmo_total, div
            else:
                children = 'KMO value is less than 0.6. Factor analysis should not proceed. The dataset should be ' \
                           'adjusted in order for factor analysis.'
                div = html.Div([html.H6(children=children, style={'color': '#4dbfff'})])
                return kmo_total, div
        elif value == 'no-pickle':
            dff = pd.read_json(df2, orient='split')
            kmo_per_item, kmo_total = calculate_kmo(dff)
            if kmo_total >= 0.6:
                children = 'KMO-value is greater than 0.6. Factor analysis may proceed.'
                div = html.Div([html.H6(children=children, style={'color': '#4dbfff'})])
                return kmo_total, div
            else:
                children = 'KMO value is less than 0.6. Factor analysis should not proceed. The dataset should be ' \
                           'adjusted in order for factor analysis.'
                div = html.Div([html.H6(children=children, style={'color': '#4dbfff'})])
                return kmo_total, div


# eigenvalues & scree plot
@app.callback([#Output('eigen-output', 'value'),
               Output('eigen-output2', 'children'),
               Output('scree-plot', 'figure'),
               Output('numFactors', 'options')],
              [Input('eigen-button', 'n_clicks')],
              [State('df-storage', 'children'),
               State('df-pm2-storage', 'children'),
               State('radio-buttons', 'value')])
def eigens(n_clicks, df1, df2, value):
    if n_clicks is None:
        raise PreventUpdate
    else:
        if value == 'yes-pickle':
            dff = pd.read_json(df1, orient='split')
            # get eigenvalues
            fa = FactorAnalyzer()
            fa.fit(dff)
            ev, v = fa.get_eigenvalues()
            # number of eigenvalues >= 1
            count = 0
            for i in range(len(ev)):
                if ev[i] > 1:
                    count = count + 1
            # scree plot
            fig = go.Figure(data=[go.Scatter(x=np.arange(1, dff.shape[1] + 1), y=ev, mode='lines+markers')])
            #radio buttons
            options = []
            for i in range(count):
                Dict = {}
                Dict['value'] = i + 1
                Dict['label'] = str(i+ 1)
                options.append(Dict)
            fig.update_layout(title_text='Scree Plot',title_x=0.5,
                              xaxis=dict(title='Factor Number'),
                              yaxis=dict(title='Eigenvalue'))
            return count, fig, options

        elif value == 'no-pickle':
            dff = pd.read_json(df2, orient='split')
            # get eigenvalues
            fa = FactorAnalyzer()
            fa.fit(dff)
            ev, v = fa.get_eigenvalues()
            # number of eigenvalues >= 1
            count = 0
            for i in range(len(ev)):
                if ev[i] > 1:
                    count = count + 1
            # scree plot
            fig = go.Figure(data=[go.Scatter(x=np.arange(1, dff.shape[1] + 1), y=ev, mode='lines+markers')])
            options = []
            for i in range(count):
                Dict = {}
                Dict['value'] = i + 1
                Dict['label'] = str(i + 1)
                options.append(Dict)
            fig.update_layout(title_text='Scree Plot',title_x=0.5,
                              xaxis=dict(title='Factor Number'),
                              yaxis=dict(title='Eigenvalue'))
            return count, fig, options


@app.callback([Output('FA-results', 'value'),
               Output('FA-results-storage', 'children'),
               Output('var-results','value'),
               Output('total-var','value')],
              [Input('FA-button', 'n_clicks')],
              [State('numFactors', 'value'),
               State('df-storage', 'children'),
               State('df-pm2-storage', 'children'),
               State('radio-buttons', 'value')])
def run_factorAnalysis(n_clicks, numFactors, df1, df2, value):
    if n_clicks is None:
        raise PreventUpdate
    if numFactors == 0:
        return "Number of factors is zero. Enter a number greater than 0 to perform factor analysis."
    else:
        if value == 'yes-pickle':
            dff = pd.read_json(df1, orient='split')
            if numFactors >= dff.shape[1]:
                return "Number of factors entered is greater than or equal to number of variables used. "
            else:
                fa = FactorAnalyzer(numFactors, rotation="varimax")
                fa.fit(dff)
                L = np.array(fa.loadings_)
                headings = list(dff.columns)
                factor_threshold = 0.25
                textual = tuple('')
                Dict = {}
                # variance, proportional variance, cumulative variance
                var, propVar, totalVar = fa.get_factor_variance()  # var not used
                for i, factor in enumerate(L.transpose()):
                    descending = np.argsort(np.abs(factor))[::-1]
                    contributions = [(np.round(factor[x], 2), headings[x]) for x in descending if
                                     np.abs(factor[x]) > factor_threshold]
                    current = 'Factor %d:' % (i + 1), contributions
                    textual = textual + current
                    Dict['Factor {}'.format(i + 1)] = contributions
                    current2 = 'Variance explained by Factor {}: '.format(i + 1) + str(propVar[i])
                    variance = variance + ', ' + current2
                    tVar = totalVar[i]
                return textual, Dict, variance[2:], tVar

        elif value == 'no-pickle':
            dff = pd.read_json(df2, orient='split')
            if numFactors >= dff.shape[1]:
                return "Number of factors entered is greater than or equal to number of variables used. "
            else:
                fa = FactorAnalyzer(numFactors, rotation="varimax")
                fa.fit(dff)
                L = np.array(fa.loadings_)
                headings = list(dff.columns)
                factor_threshold = 0.25
                textual = tuple('')
                variance = ''
                Dict = {}
                # variance, proportional variance, cumulative variance
                var, propVar, totalVar = fa.get_factor_variance() # var not used
                for i, factor in enumerate(L.transpose()):
                    descending = np.argsort(np.abs(factor))[::-1]
                    contributions = [(np.round(factor[x], 2), headings[x]) for x in descending if
                                     np.abs(factor[x]) > factor_threshold]
                    current = 'Factor %d:' % (i + 1), contributions
                    textual = textual + current
                    Dict['Factor {}'.format(i + 1)] = contributions
                    current2 = 'Variance explained by Factor {}: '.format(i+1) + str(propVar[i])
                    variance = variance + ', ' + current2
                    tVar = totalVar[i]
                return textual, Dict, variance[2:], tVar

# floorplan and bar graph options; let user choose which factor to visualize
@app.callback([Output('bar-radios', 'options'),
               Output('floorplan-radios','options')],
              [Input('FA-button', 'n_clicks')],
              [State('numFactors', 'value')])
def update_radios(n_clicks, value):
    if n_clicks is None:
        raise PreventUpdate
    else:
        options = []
        for i in range(value):
            Dict = {}
            Dict['value'] = i + 1
            Dict['label'] = 'Factor ' + str(i + 1)
            options.append(Dict)
        return options, options


# bar graph
@app.callback(Output('bar-graph', 'figure'),
              [Input('bar-graph-button', 'n_clicks')],
              [State('FA-results-storage', 'children'),
               State('bar-radios', 'value')])
def bar_graph(n_clicks, results, value):
    if n_clicks is None:
        raise PreventUpdate
    else:
        current = results['Factor {}'.format(value)]  # list
        x = []  # stores names
        y = []  # stores respective values
        for i in range(len(current)):
            number = current[i][0]
            name = current[i][1]
            x.append(name)
            y.append(number)

        fig = go.Figure(data=[go.Bar(
            x=x, y=y,
            text=y,
            textposition='auto',
        )])
        fig.update_layout(title_text='Factor Analysis Parameter Weightings for Factor {}'.format(value),
                          xaxis=dict(
                              title='Parameters for Factor {}'.format(value)
                          ),
                          yaxis=dict(
                              title='Weighting for Factor {}'.format(value)
                          ))
        return fig


# update floorplan to have room names of data files uploaded
# filters data based on the radio button picked, either temp or rh correlation comparison
# colors are based on the number given as a value of the key in the data dictionary
# i.e. 'room 2': 0.8 --> 0.8 is helps determine the color
@app.callback([Output('dash-floorplan','data'),
               Output('room-name-result','children')],
              [Input('room-names-button','n_clicks')],
              [State('FA-results-storage', 'children'),
               State('floorplan-radios', 'value')]) #factors
def send_data_to_floorplan(n_clicks, results, value):
    if n_clicks is None:
        raise PreventUpdate
    else:
        current = results['Factor {}'.format(value)]  # list
        Dict = {}
        for i in range(len(current)):
            number = current[i][0]
            name = current[i][1]
            Dict[name] = number
        children = 'You selected to visualize the floorplan for Factor {}. Data has been sent to the ' \
                   'visualizer.'.format(value)
        return Dict, html.Div([html.H6(children=children, style={'color': '#4dbfff'})])


# upload polygons from prior session; upload floorplan image
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

        # upload polygons
        if button_clicked == 'shapes-upload':
            if n_clicks is None:
                raise PreventUpdate
            else:
                uploaded_shapes = pickle.load(open(path, "rb"))  # read in pickle file
                div = html.Div([html.H6(children='Uploaded polygons.', style={'color': '#4dbfff'})])
                return div, uploaded_shapes, dash.no_update, True  # dash.no_update if don't want to return anything

        # if button_clicked == 'floorplan-upload-button':
        else:
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
        return html.Div([html.H6(children=children, style={'color': '#4dbfff'})])


# ______________________________________________________________________________________________________________________
if __name__ == '__main__':
    app.run_server(debug = 'True') # runs app