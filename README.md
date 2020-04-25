# Winterthur Interfaces
The following files comprise the Winterthur Interfaces: Bounds_and_Swing_Analysis_for_One_File.py, Bounds_and_Swing_Analysis_for_Multiple_Files.py, Cross_Correlation.py, Factor_Analysis.py.

In order to run the above files:
1) Dash by Plotly must be downloaded; instructions can be found at https://dash.plotly.com/installation.
2) The dash-floorplan component must be downloaded from https://github.com/wfreinhart/dash-floorplan. 
3) The assets folder and colorbarSpectralhorz.png must be downloaded in the same folder as the interface files. 

See requirements.txt for full list of required packages.

These interfaces were tested in the Google Chrome browser.

The stylesheets found in the assests folder come from a Plotly sample app:
stylesheet1: https://github.com/plotly/dash-sample-apps/blob/master/apps/dash-oil-and-gas/assets/s1.css
stylesheet2: https://github.com/plotly/dash-sample-apps/blob/master/apps/dash-oil-and-gas/assets/styles.css

## Bounds and Swing Analysis for One File
This interface analyzes one Winterthur .pm2 file at a time.

## Bounds and Swing Analysis for Multiple Files
This interface analyzes multiple Winterthur .pm2 files at one time.

## Cross-Correlation Analysis
This interface performs cross-correlation analysis on Winterthur .pm2 files.

## Factor Analysis 
This interface runs factor analysis on .pm2 files and on .csv files.

## prepareCSV.py

prepareCSV.py is used to modify .csv files for use with Factor_Analysis.py. A .csv file can be resampled, the date range adjusted, and the columns to be examined selected. The user must directly interact with this code and edit it to name their file path, the date range, the location to save the modified csv to, and to select the columns to examine.
