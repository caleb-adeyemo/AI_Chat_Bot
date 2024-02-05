# Choosing - Current Station, Destination Station
# Input - Delay Time (Departure), Time of Day
# Output - Delay Time (Arrival)

'''
Each model:
    From station i to station j

Each row:
    ptd(station i), dep_at(station i), dep_del(station i), pta(station j), arr_at(station j), arr_del(station j), day_hr(station i)
'''

import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_squared_error
from sklearn import neighbors

DATA_PATH = "./data/2022/test_dataset.csv"
# DATA_PATH = "./data/2022/WATRLMN_WEYMTH_OD_a51_2022_1_1.csv"

def read_all_csvs():
    data = pd.read_csv("./data/2022/WATRLMN_WEYMTH_OD_a51_2022_1_1.csv")
    df = pd.DataFrame(columns=data.columns)
    for i in range(1, 13):
        DATA_PATH = f"./data/2022/WATRLMN_WEYMTH_OD_a51_2022_{i}_{i}.csv"
        new_df = pd.read_csv(DATA_PATH, dtype=object)
        df = pd.concat([df, new_df], ignore_index=True)
    return df


# Convert HOURS:MINUTES time format to minutes as int data type
def convert_time_to_mins(str, is_midnight):
    hrs, mins = [int(x) for x in str.split(':')]
    mins += hrs * 60
    if is_midnight:
        mins = mins + 1440
    return float(mins)

def convert_time_to_hrs(str):
    hrs, _ = [int(x) for x in str.split(':')]
    return float(hrs)

# Convert each row's time values to minutes
def convert_df_time_to_mins(df):
    # Iterate over each row
    for i in range(len(df.index)):
        # If cell for the specific column is not equal to 'NaN', change time format
        if (pd.notnull(df.at[i, 'pta'])):
            df.at[i, 'pta'] = convert_time_to_mins(df.at[i, 'pta'], False)
        if (pd.notnull(df.at[i, 'ptd'])):
            df.at[i, 'ptd'] = convert_time_to_mins(df.at[i, 'ptd'], False)
        if (pd.notnull(df.at[i, 'arr_at'])):
            if df.at[i, 'pta'] > 60 and convert_time_to_mins(df.at[i, 'arr_at'], False) < 60:
                df.at[i, 'arr_at'] = convert_time_to_mins(df.at[i, 'arr_at'], True)
            else:
                df.at[i, 'arr_at'] = convert_time_to_mins(df.at[i, 'arr_at'], False)
        if (pd.notnull(df.at[i, 'dep_at'])):
            if df.at[i, 'ptd'] > 60 and convert_time_to_mins(df.at[i, 'dep_at'], False) < 60:
                df.at[i, 'dep_at'] = convert_time_to_mins(df.at[i, 'dep_at'], True)
            else:
                df.at[i, 'dep_at'] = convert_time_to_mins(df.at[i, 'dep_at'], False)

# Applies z-normalisation to time values
def scale_datasets(X_train, X_test):
    standard_scaler = StandardScaler()
    X_train_scaled = pd.DataFrame(
        standard_scaler.fit_transform(X_train),
        columns=X_train.columns
    )
    X_test_scaled = pd.DataFrame(
        standard_scaler.fit_transform(X_test),
        columns=X_test.columns
    )
    return X_train_scaled, X_test_scaled

# Create new dataset for each train station pair
def create_station_dataset(df):
    new_df = pd.DataFrame(columns=['dep_tpl', 'dep_del', 'day_hr', 'arr_del'])
    for i in range(len(df.index) - 1):
        new_df_row = {
            'dep_tpl': df.iloc[i]['tpl'],
            'dep_del': df.iloc[i]['dep_del'],
            'day_hr': df.iloc[i]['day_hr'],
            'arr_del': df.iloc[i + 1]['arr_del']
        }
        new_df.loc[len(new_df)] = new_df_row
    return new_df

# # Load data set
# df = pd.read_csv(DATA_PATH)
# df.drop(columns=df.columns.difference(['tpl', 'pta', 'ptd', 'arr_at', 'dep_at']), inplace=True)
# Load all CSV data from 2022
df = read_all_csvs()
# Store all data into one CSV file for database
df.to_csv('./data/2022/WATRLMN_WEYMTH_OD_a51_2022_1-12_1-12.csv')

# df.drop(columns=df.columns.difference(['tpl', 'pta', 'ptd', 'arr_at', 'dep_at']), inplace=True)
#
# df.dropna(subset=['ptd', 'pta', 'dep_at', 'arr_at'], thresh=2, inplace=True)
#
# print(df)
#
# df.reset_index(drop=True, inplace=True)
#
# # Change planned times of departure/arrival to actual times of departure/arrival of first and last stations
# df['pta'] = df.apply(lambda row: row.ptd if pd.isna(row.pta) else row.pta, axis=1)
# df['ptd'] = df.apply(lambda row: row.pta if pd.isna(row.ptd) else row.ptd, axis=1)
# # Remove null values from stations
# df['dep_at'] = df.apply(lambda row: row.ptd if pd.isna(row.dep_at) else row.dep_at, axis=1)
# df['arr_at'] = df.apply(lambda row: row.pta if pd.isna(row.arr_at) else row.arr_at, axis=1)
# # Add time of day in hours
# df['day_hr'] = df.apply(lambda row: convert_time_to_hrs(str(row.dep_at)) if pd.notna(row.dep_at) else convert_time_to_hrs(str(row.arr_at)), axis=1)
#
# # Convert times to minute float format
# convert_df_time_to_mins(df)
# print("Total NaN rows: ", df.isnull().any(axis=1).sum())
#
# # Add delays of departures/arrivals
# df['dep_del'] = df.apply(lambda row: row.dep_at - row.ptd, axis=1)
# df['arr_del'] = df.apply(lambda row: row.arr_at - row.pta, axis=1)
#
# print(df)
#
# knn_data = create_station_dataset(df)
# # One hot encode tpl columns
# knn_data = pd.get_dummies(knn_data, prefix='dep_tpl', columns=['dep_tpl'])
#
# # print(stat_pair_1.head(50))
# # print(df['tpl'].unique().tolist())
# # print(len(df['tpl'].unique().tolist()))
# print("Total NaN rows: ", knn_data.isnull().any(axis=1).sum())
# print(knn_data)
#
# # X = Departure delay and time of day
# # y = Arrival delay
# X = knn_data.drop(columns=['arr_del'])
# y = knn_data['arr_del']
#
# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=1)
#
# scaler = StandardScaler()
#
# X_train_scaled = scaler.fit_transform(X_train)
# X_test_scaled = scaler.fit_transform(X_test)
#
# knn_params = {'n_neighbors': [2, 3, 4, 5, 6, 7, 8, 9]}
#
# knn = neighbors.KNeighborsRegressor()
#
# model = GridSearchCV(knn, knn_params, cv=5)
# model.fit(X_train_scaled, y_train)
# print('Model fitted')
# print(model.best_params_)
#
# # prediction = model.predict
#
# X_test['prediction'] = model.predict(X_test_scaled)
# X_test['actual'] = y_test
# print(X_test.head(50))