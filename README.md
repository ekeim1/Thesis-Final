# Winterthur Interfaces
The following files comprise the Winterthur Interfaces: Bounds_and_Swing_Analysis_for_One_File.py, Bounds_and_Swing_Analysis_for_Multiple_Files.py, Cross_Correlation.py, Factor_Analysis.py.

In order to run the above files:
1) Dash by Plotly must be downloaded; instructions can be found at https://dash.plotly.com/installation.
2) The dash-floorplan component must be downloaded from https://github.com/wfreinhart/dash-floorplan. 
3) The assets folder and colorbarSpectralhorz.png must be downloaded in the same folder as the interface files. 

Stylesheets from plotly sample dash app - cite this properly

## Bounds and Swing Analyses for One File
This interface analyzes one Winterthur .pm2 file at a time. Bounds and Swing Analyses 

## Bounds and Swing Analyses for Multiple Files

## Cross-Correlation Analysis

## Factor Analysis 

## prepareCSV.py
This file requires Pandas; for assistance, see https://pandas.pydata.org/pandas-docs/stable/getting_started/install.html.

prepareCSV.py is used to modify .csv files for use with Factor_Analysis.py. A .csv file can be resampled, the date range adjusted, and the columns to be examined selected. The user must directly interact with this code and edit it to name their file path, the date range, the location to save the modified csv to, and to select the columns to examine.
