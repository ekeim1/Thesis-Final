# Import required libraries
import pandas as pd
import dash_floorplan
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
from dash.exceptions import PreventUpdate
import base64
import io
import plotly.express as px
import pickle
import plotly.graph_objects as go

# read in colorbar image (for color scale on floorplan)
encoded_image = base64.b64encode(open('colorbarSpectralhorz.png', 'rb').read())
image_src = 'data:image/png;base64,{}'.format(encoded_image.decode())

app = dash.Dash(__name__)

# APP LAYOUT____________________________________________________________________________________________________________
app.layout = html.Div([
    # title
    html.Div([
        html.H1(children='Winterthur Cross-Correlation Interface', style={'textAlign': 'center'})
    ],style={"margin-bottom": "25px"}),

    # upload files
    html.Div([
        html.H6('Please upload the files you wish to compare.'),
        dcc.Upload(
            html.Button('Upload files'),
            id='many-files-upload',
            style={'display': 'inline-block'},
            multiple=True
        ),
        html.Div(id='output-many-upload', style={'display': 'inline-block'}),
        html.H6(id='temp-df-storage', style={'display': 'none'}),
        html.H6(id='RH-df-storage', style={'display': 'none'})
    ],className='pretty_container twelve columns'),

    # run correlation
    html.Div([
        html.Button(id='run-cross-corr', children='Run cross-correlation'),
        # see correlation results as a table
        html.Div(id='cross-corr-output', style={'display': 'inline-block'}),
        html.Div(id='corr-temp-storage', style={'display': 'none'}),
        html.Div(id='corr-RH-storage', style={'display': 'none'}),
    ],className='pretty_container twelve columns'),

    # select temp or rh; make graphs: heatmap and scatter plot matrix
    html.Div([
        html.H6('Please select whether you want to visualize temperature or relative humidity cross-correlation.'),
        dcc.RadioItems(
            id='radio-buttons',
            options=[
                {'label': 'Visualize temperature correlation.', 'value': 'temp'},
                {'label': 'Visualize relative humidity correlation.', 'value': 'rh'}
            ],
            value='temp'
        ),
        html.H6('Click the button corresponding to the graph you would like to make.'),
        html.Button(id='make-heatmap', children='Make heatmap'),
        html.Button(id='make-scatter', children='Make scatter plot matrix')
    ],className='pretty_container twelve columns'),

    # heatmap
    html.Div([
        html.H5('Heatmap'),
        html.H6('Hover over a square to see the correlation value.'),
        dcc.Graph(id='heatmap')
    ],className='pretty_container twelve columns'),
    # scatter plot matrix
    html.Div([
        html.H5('Scatter Matrix'),
        dcc.Graph(id='scatter')
    ],className='pretty_container twelve columns'),

    # visualization
    html.H1('Visualize'),
    html.Div([
        html.Div([
            # radio buttons
            html.H6('Please select whether you want to visualize temperature or relative humidity cross-correlation.'),
            dcc.RadioItems(
                id='radio-buttons2',
                options=[
                    {'label': 'Temperature.', 'value': 'temp'},
                    {'label': 'Relative Humidity', 'value': 'rh'}
                ],
                value='temp'
            ),
            html.H6('Please select which room you want to be the "main" room, the room that you compare all other '
                    'files to.'),
            dcc.RadioItems(id='radio-buttons3'),

            html.Button(id='room-names-button', children='Submit'),  # 'Click to send correlation data to visualizer.'),
            html.Div(id='room-name-result'),
        ],className='pretty_container five columns'),

        # input floorplan image
        html.Div([
            html.H6('Upload your floorplan image below. Type the url of the Google Drawing containing your image and click the '
                    'button. Only Google Drawings and urls ending in .jpg, .png will work. To work with multiple images, put '
                    'them all in the same Google Drawing. Make sure your Google Drawing is published to the web, which can be '
                    'done by clicking "File", "Publish to the web", selecting the image size, and hitting "Publish".'
                    ' Copy the link given and paste it below. Make sure to unpublish the image if you do not want other to '
                    'access it when you are done using this application.'),
            dcc.Input(id='floorplan-image-input', value=''),
            html.Button(id='floorplan-upload-button', children='Upload floorplan image.'),
        ], className='pretty_container seven columns'),
    ],className="row flex-display"),

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
    ], className='pretty_container twelve columns'),

    # dash floorplan components
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
# make .pm2 file into a df
def make_df_pm2(filename, contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_table(io.BytesIO(decoded), skiprows=[0, 1, 3])
    df['DATE AND TIME GMT'] = pd.to_datetime(df['DATE AND TIME GMT'])  # set date and time column as datetime type
    df.columns = ['Date and Time in GMT', 'Temperature (Degrees Fahrenheit)', 'Relative Humidity (%)']  # rename columns
    df = df.set_index('Date and Time in GMT')
    # resample data to fill in any gaps and to ensure same time interval
    upsampledTemp = df['Temperature (Degrees Fahrenheit)'].resample('15min').mean()
    interpolatedTemp = upsampledTemp.interpolate(method='linear')
    upsampledRH = df['Relative Humidity (%)'].resample('15min').mean()
    interpolatedRH = upsampledRH.interpolate(method='linear')
    frame = {'Temp_{}'.format(filename): interpolatedTemp, 'RH_{}'.format(filename): interpolatedRH}
    result = pd.DataFrame(frame)
    return result


# CALLBACKS_____________________________________________________________________________________________________________
# upload comparison files and run cross-correlation
@app.callback([Output('output-many-upload', 'children'),  # output that files were uploaded and corr was run
               Output('temp-df-storage', 'children'),  # hidden div
               Output('RH-df-storage', 'children')],  # hidden div
              [Input('many-files-upload', 'filename')],
              [State('many-files-upload', 'contents')])
def read_in_files(list_filenames, list_contents):
    if list_filenames is not None:
        df_temp = pd.DataFrame()
        df_RH = pd.DataFrame()
        # run cross corr
        for filename, contents in zip(list_filenames, list_contents):
            df = make_df_pm2(filename, contents)
            df_temp['Temp_{}'.format(filename)] = df['Temp_{}'.format(filename)]
            df_RH['RH_{}'.format(filename)] = df['RH_{}'.format(filename)]
        # drop rows with NaN in them
        df_temp.dropna(inplace=True)
        df_RH.dropna(inplace=True)
        children = 'Files have been uploaded.'
        div = html.Div([html.H6(children=children, style={'color': '#4dbfff'})])
        return div, df_temp.to_json(date_format='iso', orient='split'), df_RH.to_json(date_format='iso',
                                                                                           orient='split')


# run cross-correlation
@app.callback([Output('corr-temp-storage', 'children'),  # hidden div
               Output('corr-RH-storage', 'children'),  # hidden div
               Output('cross-corr-output', 'children'),  # output that corr was run
               Output('radio-buttons3', 'options')],
              [Input('run-cross-corr', 'n_clicks')],
              [State('temp-df-storage', 'children'),
               State('RH-df-storage', 'children')])
def run_cross_corr(n_clicks, temp_df, rh_df):
    if n_clicks is None:
        raise PreventUpdate
    else:
        # temp
        df_temp = pd.read_json(temp_df, orient='split')
        temp_corr = df_temp.corr()
        # rh
        df_RH = pd.read_json(rh_df, orient='split')
        RH_corr = df_RH.corr()

        names = list(temp_corr.columns)
        options = []
        for i in range(len(names)):
            Dict = {}
            Dict['value'] = names[i]
            names[i] = names[i].replace('Temp_', '')
            Dict['label'] = names[i]
            options.append(Dict)
        children = 'Cross-correlation was run.'
        div = html.Div([html.H6(children=children, style={'color': '#4dbfff'})])
        return temp_corr.to_json(date_format='iso', orient='split'), \
               RH_corr.to_json(date_format='iso', orient='split'), div, options


# make heatmap
@app.callback(Output('heatmap', 'figure'),
              [Input('make-heatmap', 'n_clicks')],
              [State('corr-temp-storage', 'children'),
               State('corr-RH-storage', 'children'),
               State('radio-buttons', 'value')])
def make_graph(n_clicks, corrT, corrRH, value):
    if n_clicks is None:
        raise PreventUpdate
    else:
        if value == 'temp':
            corr_temp = pd.read_json(corrT, orient='split')
            fig1 = go.Figure(data=go.Heatmap(z=corr_temp.values.tolist(), x=corr_temp.columns.tolist(),
                                             y=corr_temp.columns.tolist(), colorscale='Spectral'))
            fig1.update_yaxes(autorange="reversed")
            # fig1.update_xaxes(side='top')
            fig1.update_layout(title='Temperature Correlation Values')
            return fig1
        else:  # value == 'rh'
            corr_rh = pd.read_json(corrRH, orient='split')
            fig1 = go.Figure(data=go.Heatmap(z=corr_rh.values.tolist(), x=corr_rh.columns.tolist(),
                                             y=corr_rh.columns.tolist(), colorscale='Spectral'))
            fig1.update_yaxes(autorange="reversed")
            # fig1.update_xaxes(side='top')
            fig1.update_layout(title='Relative Humidity Correlation Values')
            return fig1

# make scatter plot matrix
@app.callback(Output('scatter', 'figure'),
              [Input('make-scatter', 'n_clicks')],
              [State('radio-buttons', 'value'),
               State('temp-df-storage', 'children'),
               State('RH-df-storage', 'children')])
def make_graph(n_clicks, value, temp_df, rh_df):
    if n_clicks is None:
        raise PreventUpdate
    else:
        if value == 'temp':
            temp_df = pd.read_json(temp_df, orient='split')
            fig2 = px.scatter_matrix(temp_df, title='Correlation Matrix of Temperature')
            fig2.update_layout(height=1024)  # width=1000
            # fig2.update_layout(xaxis_tickangle=45, yaxis_tickangle=-45)
            return fig2
        else:  # value == 'rh'
            rh_df = pd.read_json(rh_df, orient='split')
            fig2 = px.scatter_matrix(rh_df, title='Correlation Matrix of Relative Humidity')
            return fig2
            # fig2.update_layout(height=1024)#width=1000,


# update floorplan to have room names of data files uploaded
# filters data based on the radio button picked, either temp or rh correlation comparison
# colors are based on the number given as a value of the key in the data dictionary
# i.e. 'room 2': 0.8 --> 0.8 is helps determine the color
@app.callback([Output('dash-floorplan', 'data'),
               Output('room-name-result', 'children')],
              [Input('room-names-button', 'n_clicks')],
              [State('corr-temp-storage', 'children'),
               State('corr-RH-storage', 'children'),
               State('radio-buttons2', 'value'),  # temp or rh
               State('radio-buttons3', 'value')])  # "main" room
def send_data_to_floorplan(n_clicks, corr_temp, corr_rh, value, room):
    if n_clicks is None:
        raise PreventUpdate
    else:
        Dict = {}
        if value == 'temp':
            corr_temp = pd.read_json(corr_temp, orient='split')
            names = list(corr_temp.columns)
            selection = corr_temp[room]  # for RH replace 'Temp_' with 'RH_'
            for i in range(selection.shape[0]):
                Dict[names[i]] = selection[i]
            children = 'You selected to visualize the floorplan with Temperature correlation and with {} as your "main"' \
                       ' room file.'.format(room)
            div = html.Div([html.H6(children=children, style={'color': '#4dbfff'})])
            return Dict, div
        else:
            corr_RH = pd.read_json(corr_rh, orient='split')
            names = list(corr_RH.columns)
            room = room.replace('Temp_', 'RH_')  # for RH replace 'Temp_' with 'RH_'
            selection = corr_RH[room]
            for i in range(selection.shape[0]):
                Dict[names[i]] = selection[i]
            print(Dict)
            children = 'You selected to visualize the floorplan with Relative Humidity correlation and with {} as your' \
                       ' "main" room file.'.format(room)
            div = html.Div([html.H6(children=children, style={'color': '#4dbfff'})])
            return Dict, div


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
                div = html.Div([html.H6(children='Uploaded poylgons.', style={'color': '#4dbfff'})])
                return div, uploaded_shapes, dash.no_update, True  # dash.no_update if don't want to return anything

        # if button_clicked == 'floorplan-upload-button':
        else:
            if n_clicks2 is None:
                raise PreventUpdate
            else:
                image = value + ''  # to ensure string
                return dash.no_update, dash.no_update, image, True


# save polygons to use again later
@app.callback(Output('save-points-output', 'children'),
              [Input('save-points', 'n_clicks')],
              [State('save-points-input', 'value'),
               State('dash-floorplan', 'shapes')])
def save_points(n_clicks, value, shapes):
    if n_clicks is None:
        raise PreventUpdate
    else:
        path = value + '.pickle'  # add .pickle to name
        pickle.dump(shapes, open(path, "wb"))  # save as pickle file
        children = 'File has been saved at the following location: ' + path
        div = html.Div([html.H6(children=children, style={'color': '#4dbfff'})])
        return div


# ______________________________________________________________________________________________________________________
if __name__ == '__main__':
    app.run_server(debug = 'True') # runs app