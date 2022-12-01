from tabnanny import check
from flask import Flask, render_template, request, redirect,session, json,redirect,url_for
import sqlite3
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import tensorflow as tf
import os
import pandas as pd
import numpy as np

from pandas import read_csv
from datetime import datetime
from math import sqrt
from numpy import concatenate
from matplotlib import pyplot
from pandas import read_csv
from pandas import DataFrame
from pandas import concat
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
import math

new_model1 = tf.keras.models.load_model('predict1ppm')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///monitor.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'This is a secret key required for session'
db = SQLAlchemy(app)



class Login(db.Model):
    username = db.Column(db.String(100), primary_key=True)
    password = db.Column(db.String(100))




@app.route('/', methods=['GET', 'POST'])
def start0():
    return render_template('login.html')

@app.route('/login.html', methods=['GET', 'POST'])
def start():
    if request.method=='POST':
        formUsername = request.form['username']
        formPassword = request.form['password']
        row  = Login.query.filter_by(username = formUsername).first()
        if row is None:
            return render_template('login.html',check1=True,check2=False)
        else:
            if row.password == formPassword:
                session['username'] =  formUsername
                return render_template('index.html',username = session['username'])
            else:
                return render_template('login.html',check1=False,check2=True)
    return render_template('login.html')

@app.route('/index.html', methods=['GET', 'POST'])
def index():
    if request.method=='POST':
        df = pd.read_csv('https://api.thingspeak.com/channels/1170558/feeds.csv?results=60') 
        df.rename(columns = {'field1' : 'CO2', 'field2' : 'Temperature','field3':'Humidity','created_at':'Date'}, inplace = True)
        df.set_index('Date', inplace=True)
        df.index.name = 'Date'
        df = df.drop('entry_id', 1)
        dataset = df
        # specify columns to plot
        groups = [0, 1, 2]
        # convert series to supervised learning
        def series_to_supervised(data, n_in=1, n_out=1, dropnan=True):
            n_vars = 1 if type(data) is list else data.shape[1]
            df = DataFrame(data)
            cols, names = list(), list()
            # input sequence (t-n, ... t-1)
            for i in range(n_in, 0, -1):
                cols.append(df.shift(i))
                names += [('var%d(t-%d)' % (j+1, i)) for j in range(n_vars)]
            # forecast sequence (t, t+1, ... t+n)
            for i in range(0, n_out):
                cols.append(df.shift(-i))
                if i == 0:
                    names += [('var%d(t)' % (j+1)) for j in range(n_vars)]
                else:
                    names += [('var%d(t+%d)' % (j+1, i)) for j in range(n_vars)]
            # put it all together
            agg = concat(cols, axis=1)
            agg.columns = names
            # drop rows with NaN values
            if dropnan:
                agg.dropna(inplace=True)
            return agg

        values = dataset.values
        # integer encode direction
        encoder = LabelEncoder()
        values[:,2] = encoder.fit_transform(values[:,2])
        # ensure all data is float
        values = values.astype('float32')
        # normalize features
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled = scaler.fit_transform(values)
        # frame as supervised learning
        reframed = series_to_supervised(scaled, 1, 1)
        # drop columns we don't want to predict
        reframed.drop(reframed.columns[[4,5]], axis=1, inplace=True)
        print(reframed.head())

        values = reframed.values
        n_train_mins = 30
        train = values[:n_train_mins, :]
        test = values[n_train_mins:, :]
        # split into input and outputs
        train_X, train_y = train[:, :-1], train[:, -1]
        test_X, test_y = test[:, :-1], test[:, -1]
        # reshape input to be 3D [samples, timesteps, features]
        train_X = train_X.reshape((train_X.shape[0], 1, train_X.shape[1]))
        test_X = test_X.reshape((test_X.shape[0], 1, test_X.shape[1]))
        #print(train_X.shape, train_y.shape, test_X.shape, test_y.shape)

        forecast = new_model1.predict(train_X[-30:])
        forecast_repeated = np.repeat(forecast, scaled.shape[1], axis=1)
        y_forecasted = scaler.inverse_transform(forecast_repeated)[:,0]
        labels = list(range(1,31))
        values = list(y_forecasted)

        ppm = math.ceil(np.mean(y_forecasted))

        return render_template('index.html',ppm=ppm,labels=labels,values=values,check=True)
    return render_template('index.html',check=False)



    
if __name__ == "__main__":
    app.run(debug=True)
