import pandas as pd

# user lists their file path HERE:
file = "exterior weather 2011-1-1-to-2020-3-1.csv"
# user inputs dates to examine HERE:
startDate = '2015-07-02 13:30'
endDate = '2020-02-06 17:30'
# user inputs location to save csv to HERE:
saveFileHere = 'E:\interpolated_data.csv'

df = pd.read_csv(file)  # replace specific file with variable from upload

# user selects parameter to extract HERE:
# user can change these based on their weather data file, but a 'date' column must be included
# the names of columns must correspond to the column names in the csv file exactly
df = df[['DATE', # this column must be present; if name is different, make sure to change here and in later lines of code
         'HourlyDewPointTemperature',
         'HourlyDryBulbTemperature',
         'HourlyPrecipitation',
         'HourlyRelativeHumidity',
         'HourlyStationPressure',
         'HourlyVisibility',
         'HourlyWetBulbTemperature',
         'HourlyWindSpeed']]

df['DATE'] = df['DATE'].astype('datetime64[ns]') # date column

# loop through numerical data
for i in range(len(df.columns) - 1):
    df[df.columns[i+1]] = df[df.columns[i+1]].astype('float64')

df = df.set_index('DATE') # set date column as the index

# resample
frame = {}
for i in range(len(df.columns) - 1):
    upsampled = df[df.columns[i+1]].resample('15min').mean() # user can change sampling rate
    interpolated = upsampled.interpolate(method='linear')
    frame[df.columns[i+1]] = interpolated

result = pd.DataFrame(frame) # make dataframe from interpolated data
# select only the dates desired
result = result.loc[startDate : endDate]

# save to csv
result.to_csv(saveFileHere)
