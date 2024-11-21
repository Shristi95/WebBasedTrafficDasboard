import pandas as pd
import geopandas
# import requests
import json
import numpy as np

# jsonurl= "C:\\Users\\paudel\\Desktop\\DashboardEx\\00FinalDashboard\\data\\raw\\fn-filterr.json"
jsonurl = "C:\\Users\\paudel\\Desktop\\DashboardEx\\00FinalDashboard\\data\\raw\\fn-poicfg_trafficFlow.json" ### Change this to read file from local computer

# open and load json file
f = open(jsonurl,encoding='utf-8')
data = json.load(f)

# flattened df
# , sep='_')  #before I replace . in column names with _
fdf = pd.json_normalize(data, sep='_') 


# select few necessary columns only
selected_columns = ['enmea_std_guid',
                    'enmea_poi_addrCsv_street',
                    'enmea_poi_addrCsv_city',
                    'enmea_poi_addrCsv_state',
                    'enmea_std_ts',
                    'enmea_poi_inductionLoopId',
                    'enmea_poi_vehicleFlowRate',
                    'enmea_poi_vehicleFlowRatePerSecond',
                    'enmea_poi_vehicleFlowRatePerMinute',
                    'enmea_poi_occupancyPercentage',
                    'enmea_std_loc_lat',
                    'enmea_std_loc_lon']

# create new df with selected columns
df = fdf[selected_columns]

# check data type of columns in new df
print(df.dtypes)

# #check missing values if any
# print(new_fdf.isna().any())

# convert datatype of some columns
convert_dict = {'enmea_poi_vehicleFlowRate': int,
                'enmea_poi_vehicleFlowRatePerSecond': float,
                'enmea_poi_vehicleFlowRatePerMinute': float,
                'enmea_poi_occupancyPercentage': float,
                'enmea_std_loc_lat':'string',
                'enmea_std_loc_lon':'string'
                }

df = df.astype(convert_dict)
# print(df.dtypes)

# convert date to proper format
df['enmea_std_ts'] = pd.to_datetime(df['enmea_std_ts'])

# print (df)

# replace spaces in sensor ID with underscores(_)
df['enmea_std_guid'] = df['enmea_std_guid'].str.replace(" ", "_")

# ####################################################################### data preprocessing before aggregating- start-------------------
#### 1) convert to german umlauts/unicode to english characters
df["enmea_poi_addrCsv_street"] = df["enmea_poi_addrCsv_street"].str.replace("ä", "ae").str.replace("ö", "oe").str.replace("ü", "ue").str.replace("ß", "ss")


##### 2) error correction (3 types of errors)

#1. Correct lat/long of fn/tfMQ_FD238_D07_Z1.1_FD238_D07_Z1.1 sensor
# original lat_lon: 47.661545    9.474228
# corrected lat_lon: 47.661545	9.474256  -- change lon only (lat is same)

for i in df.index: 
    if df.loc[i,"enmea_std_guid"] == "fn/tfMQ_FD238_D07_Z1.1_FD238_D07_Z1.1": 
        # print (df.loc[i,"enmea_std_loc_lon"])
        df.loc[i,"enmea_std_loc_lon"] = "9.474256"
        # print(df.loc[i,"enmea_std_loc_lon"])

#2. Correct street name of fn/tfMQ_FD230_D01_D11_FD230_D01_D11 sensor 
for i in df.index: 
    if df.loc[i,"enmea_std_guid"] == "fn/tfMQ_FD230_D01_D11_FD230_D01_D11": 
          df.loc[i,"enmea_poi_addrCsv_street"] = "Maybachplatz"
    
#3. Correct ts ---remove duplicated data of 26 sensors with ts like- '2022-11-20T17:11:01.000Z' (i.e. sending data at 00z seconds of any min)
#solution- I simply removed all the duplicate rows from dataframe
print ('original_number of rows', len(df.index)) #original rows= 250415
df= df.drop_duplicates()
print ('rows_after_removing duplicates', len(df.index)) #remaining rows= 85505  -- but how?? 

##########
# # view sensors ids using drop duplicates
# rdf= df.drop_duplicates(subset=['enmea_std_guid'])
# print (rdf)

##### 3) Add excel file with lanes and road info and connect to this df!! 
# Read the external excel file and store it in a dataFrame -- and select necessary columns
excelpath= "C:\\Users\\paudel\\Desktop\\DashboardEx\\00FinalDashboard\\data\\sensorslist.xlsx"  #change this to get file from local computer
excel_df = pd.read_excel(excelpath, sheet_name='datacorrected')
excel_df_subset = excel_df[['enmea_std_guid','new_id','lanes','road_type','max_speed_edited']].copy()
# print(excel_df_subset)

#merge the exceldf to json df
df = pd.merge(df, excel_df_subset, on='enmea_std_guid')
# print(df)


# ####################################################################### data preprocessing before aggregating- end---------
# print(df)
# give aggregation rule
aggregation_rule = {
    'enmea_poi_addrCsv_street':'first',
    'enmea_poi_addrCsv_city':'first',
    'enmea_poi_addrCsv_state':'first',
    'enmea_poi_inductionLoopId':'first',
    'enmea_poi_vehicleFlowRate':'sum', #'mean'
    'enmea_poi_vehicleFlowRatePerSecond':'sum', #'mean'   ## I am doing sum- cause I want to show total vehicles in 1 hr
    'enmea_poi_vehicleFlowRatePerMinute':'sum', #'mean' 
    'enmea_poi_occupancyPercentage':'mean', ## mean- cause I want to show average occupancy per min. 
    'enmea_std_loc_lat':'first',
    'enmea_std_loc_lon':'first',
    'new_id':'first',
    'lanes':'first',
    'road_type':'first',
    'max_speed_edited':'first'
}

print(df)

#filter selected sensors only for minute dashboard
sensors= ['fn/tfMQ_FD227_D04_D5_FD227_D04_D5','fn/tfMQ_FD227_D06_D7_FD227_D06_D7','fn/tfMQ_FD227_D08_D9_FD227_D08_D9']
if 'enmea_std_guid' in df.columns:
    filtered_df = df.loc[df['enmea_std_guid'].isin(sensors)]
    print(filtered_df)
else:
    print("enmea_std_guid column does not exist")

# for leaflet 
timestamp= '2022-11-21 00:04'
copydf= df  #first generate copy of df so that original df remains untouched/unmodified
copydf['enmea_std_ts_string'] = copydf['enmea_std_ts'].astype(str)
copydf['enmea_std_ts_sliced'] = copydf['enmea_std_ts_string'].str[0:16]

# copydf['enmea_std_ts'] = copydf['enmea_std_ts'].astype(str)
# copydf['enmea_std_ts'] = copydf['enmea_std_ts'].str[0:16]

print(copydf['enmea_std_ts_string'].str[0:16])
leaflet_df = copydf[copydf['enmea_std_ts_sliced'] == timestamp] #saving data of one row only of each sensor for loading in leaflet (40 rows)
# leaflet_df = copydf[copydf['enmea_std_ts'] == timestamp]
print(leaflet_df)
# slice the last letters, check it and create -direction column to put direction 
last_5_chars = leaflet_df['new_id'].str[-6:]
leaflet_df['direction'] = np.where(last_5_chars.str.endswith('f'), 'forward',
                    np.where(last_5_chars.str.endswith('fl'), 'forward left',
                        np.where(last_5_chars.str.endswith('fr'), 'forward right',
                            np.where(last_5_chars.str.endswith('b'), 'backward',
                                    np.where(last_5_chars.str.endswith('bl'), 'backward left',
                                             np.where(last_5_chars.str.endswith('br'), 'backward right', ''))))))


# group data by sensorid -->  aggregated data (of each sensor) at diff time interval  --> round off decimal values
# ///////////////////////////
dailydf = df.groupby('enmea_std_guid').resample('D', on= 'enmea_std_ts').agg(aggregation_rule).round(1)       # Daily
# df = df.groupby('enmea_std_guid').resample('15min', on= 'enmea_std_ts').agg(aggregation_rule).round(1)    # 15min

df = df.groupby('enmea_std_guid').resample('H', on='enmea_std_ts').agg(
    aggregation_rule).round()           # Hourly
# df = df.groupby('enmea_std_guid').resample('2H', on= 'enmea_std_ts').agg(aggregation_rule).round(1)    # 2 Hour

######this code runs- but I did this in javascript for heatmap only
# #sorted to show data later in heat map by in sorted order
# df=df.sort_values(by='enmea_poi_addrCsv_street')  
###test


# print (df)

# creating geodataframe
# creating point layer
gdf= geopandas.GeoDataFrame(
    df, geometry=geopandas.points_from_xy(df.enmea_std_loc_lon, df.enmea_std_loc_lat))# give lat and lon attribute for making point geometry

# print(gdf.head())
# print(gdf.tail())
# print(gdf)
# # for idx, row in gdf.iterrows():
# #     print(row)

# save to geojson file
# gdf.to_file('./data/aggregated/fifteen_min.json', driver="GeoJSON")   # 15min
gdf.to_file('./data/aggregated/hourly.json',
            driver="GeoJSON")          # Hourly
# gdf.to_file('./data/aggregated/two_hour.json', driver="GeoJSON")      # 2 Hour
# gdf.to_file('./data/aggregated/daily.json', driver="GeoJSON")          # Daily


# ////////////////////////////// Code for daily aggregation //////////////////////-///////////////////////////////////////
print(dailydf.columns)

daily_gdf= geopandas.GeoDataFrame(
    dailydf, geometry=geopandas.points_from_xy(dailydf.enmea_std_loc_lon, dailydf.enmea_std_loc_lat))# give lat and lon attribute for making point geometry
daily_gdf.to_file('./data/aggregated/daily.json',
            driver="GeoJSON")          # daily


# ////////////////////////////// Code for daily aggregation -///////////////////////////////////////////////////////////


# # //////////////////////////////Code for saving minute data by filtering some sensors only -- start now /////////////////////////////////////////////////

minute_gdf= geopandas.GeoDataFrame(
   filtered_df, geometry=geopandas.points_from_xy(filtered_df.enmea_std_loc_lon, filtered_df.enmea_std_loc_lat))# give lat and lon attribute for making point geometry
minute_gdf.to_file('./data/aggregated/minute.json',
            driver="GeoJSON")          # min

# # ////////////////////////////////Code for saving minute data by filtering some sensors only --end--////////////////////////////////////////////////////

# save one layer for leaflet-- with only one row from each sensors ------ 

leaflet_gdf= geopandas.GeoDataFrame(
   leaflet_df, geometry=geopandas.points_from_xy(leaflet_df.enmea_std_loc_lon, leaflet_df.enmea_std_loc_lat))# give lat and lon attribute for making point geometry
leaflet_gdf.to_file('./data/aggregated/leaflet.json',
            driver="GeoJSON")    


f.close()


# arcgis pro code to convert iso time to normal date 
# from datetime import datetime
# def datee(x): 
#     # Convert the date string to a datetime object
#     datetime_object = datetime.strptime(x, "%Y-%m-%dT%H:%M:%S.%fZ")

# # Format the datetime object as a normal date string
#     normal_date = datetime_object.strftime("%Y-%m-%d %H:%M:%S")
#     return normal_date
