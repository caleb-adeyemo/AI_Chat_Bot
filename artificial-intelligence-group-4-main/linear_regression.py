import os
from datetime import time
from sklearn.linear_model import LinearRegression
from sklearn import neighbors
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_squared_error
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import psycopg2

load_dotenv()       # Load .env file with PostgreSQL details
# Connect to PostgreSQL database
connect = psycopg2.connect(
    host=os.environ.get("PGHOST"),
    user=os.environ.get("PGUSER"),
    password=os.environ.get("PGPASSWORD"),
    database=os.environ.get("PGDATABASE"),
    port=os.environ.get("PGPORT")
)

cursor = connect.cursor()   # Cursor object for performing SQL queries

# cursor.execute("SELECT s.name, s.tpl FROM stations s INNER JOIN (SELECT DISTINCT ON (tpl) tpl FROM train_data)t ON s.tpl = t.tpl")

def get_train_data():
    # Get all column names in train_data database
    cursor.execute('SELECT column_name FROM information_schema.columns\
                    WHERE table_name = %s AND table_schema = %s', ('train_data', 'public'))

    # Convert list of tuples to list
    columns = [item for t in cursor.fetchall() for item in t]

    # Get all train data
    cursor.execute("SELECT * FROM train_data")
    # Create dataframe for prediction model using train data from PostgreSQL
    df = pd.DataFrame(cursor.fetchall(), columns=columns)
    # Remove 'id' column
    df.drop('id', axis=1, inplace=True)
    return df

def convert_time_to_minutes(time_obj):
    if isinstance(time_obj, time):
        time_str = time_obj.strftime("%H:%M")
        parts = list(map(int, time_str.split(':')))
        if len(parts) == 3:
            hours, minutes, _ = parts
        else:
            hours, minutes = parts
        return hours * 60 + minutes
    return np.nan

def predict_arrival_time_lr(stationA, stationB, dep_delay, planned_arrival_time):
    df = get_train_data()
    stationA_data = df[df['tpl'] == stationA].copy()
    stationB_data = df[df['tpl'] == stationB].copy()

    stationA_data['dep_delay'] = stationA_data['dep_at'].apply(convert_time_to_minutes) - stationA_data['ptd'].apply(convert_time_to_minutes)
    stationA_data['time_of_day'] = stationA_data['ptd'].apply(lambda x: convert_time_to_minutes(x) // 60)
    stationB_data['arr_delay'] = stationB_data['arr_at'].apply(convert_time_to_minutes) - stationB_data['pta'].apply(convert_time_to_minutes)

    # Merge dataframes on 'rid'
    merged_df = pd.merge(stationA_data[['rid', 'dep_delay', 'time_of_day']], stationB_data[['rid', 'arr_delay']], on='rid', how='inner')

    # Remove rows with NaN values
    merged_df.dropna(subset=['dep_delay', 'time_of_day', 'arr_delay'], inplace=True)

    X = merged_df[['dep_delay', 'time_of_day']].values
    y = merged_df['arr_delay'].values

    # Train test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)

    # Linear regression
    reg = LinearRegression().fit(X_train, y_train)

    y_pred = reg.predict(X_test)

    mse = mean_squared_error(y_test, y_pred)

    rmse = np.sqrt(mse)
    # print(f'LR Model RMSE: {rmse}')

    # Get current time of day
    current_time_of_day = pd.to_datetime('now').hour

    # Predict
    predicted_arr_delay = reg.predict(np.array([[dep_delay, current_time_of_day]]))

    # Convert planned arrival time to datetime object
    planned_arrival_time = pd.to_datetime(planned_arrival_time, format='%H:%M')

    # Add predicted delay to planned arrival time
    actual_arrival_time = planned_arrival_time + pd.Timedelta(minutes=predicted_arr_delay[0])

    return actual_arrival_time.strftime('%H:%M')

def predict_arrival_time_knn(stationA, stationB, dep_delay, planned_arrival_time):
    df = get_train_data()

    stationA_data = df[df['tpl'] == stationA].copy()
    stationB_data = df[df['tpl'] == stationB].copy()

    stationA_data['dep_delay'] = stationA_data['dep_at'].apply(convert_time_to_minutes) - stationA_data['ptd'].apply(convert_time_to_minutes)
    stationA_data['time_of_day'] = stationA_data['ptd'].apply(lambda x: convert_time_to_minutes(x) // 60)
    stationB_data['arr_delay'] = stationB_data['arr_at'].apply(convert_time_to_minutes) - stationB_data['pta'].apply(convert_time_to_minutes)

    # Merge dataframes on 'rid'
    merged_df = pd.merge(stationA_data[['rid', 'dep_delay', 'time_of_day']], stationB_data[['rid', 'arr_delay']], on='rid', how='inner')

    # Remove rows with NaN values
    merged_df.dropna(subset=['dep_delay', 'time_of_day', 'arr_delay'], inplace=True)

    X = merged_df[['dep_delay', 'time_of_day']].values
    y = merged_df['arr_delay'].values

    # Train test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)

    # KNN regression
    knn_params = {'n_neighbors': [2, 3, 4, 5, 6, 7, 8, 9]}
    knn = neighbors.KNeighborsRegressor()
    knn_reg = GridSearchCV(knn, knn_params, cv=5).fit(X_train, y_train)
    y_pred = knn_reg.predict(X_test)

    mse = mean_squared_error(y_test, y_pred)

    rmse = np.sqrt(mse)
    # print(f'KNN Model RMSE: {rmse}')

    # Get current time of day
    current_time_of_day = pd.to_datetime('now').hour

    # Predict
    predicted_arr_delay = knn_reg.predict(np.array([[dep_delay, current_time_of_day]]))

    # Convert planned arrival time to datetime object
    planned_arrival_time = pd.to_datetime(planned_arrival_time, format='%H:%M')

    # Add predicted delay to planned arrival time
    actual_arrival_time = planned_arrival_time + pd.Timedelta(minutes=predicted_arr_delay[0])

    return actual_arrival_time.strftime('%H:%M')

print(predict_arrival_time_lr('WOKING', 'BSNGSTK', 10, '23:30'))
# print(predict_arrival_time_knn('WOKING', 'BSNGSTK', 10, '23:30'))
