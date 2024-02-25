import flask
import os
import pandas as pd
import datetime
import pickle

from flask import request

from tsfresh import extract_features
from tsfresh.utilities.dataframe_functions import impute
from tsfresh.feature_extraction import ComprehensiveFCParameters

app = flask.Flask(__name__, static_url_path = "")
partners = []

@app.route('/')
def main():
    """Переадресация на красивую картинку"""
    return flask.send_from_directory(".", path="index.html")

@app.route('/api/partners', methods = ['POST'])
def createPartner():
    """Реализация Post (новый партнёр)"""
    partner = {
        'id': len(partners),
        'name': request.json['name'],
        'budget': request.json['budget'],
        'spent_budget': 0,
        'is_stopped': False,
        'data': pd.DataFrame({'id': pd.Series(dtype='int'),
                   'cashback': pd.Series(dtype='int'),
                   'date': pd.Series(dtype='datetime64[ns]')}),
        'datestop': datetime.datetime(8999, 1, 1)
    }
    partners.append(partner)
    return flask.jsonify({i:partner[i] for i in partner if i not in ['data', 'is_stopped']}), 201

@app.route('/api/partners/<int:idp>', methods = ['GET'])
def getPartner(idp):
    """Реализация Get (информация о партнёре)"""
    if not partners[idp]['is_stopped']:
        partners[idp]['is_stopped'] = off(idp)
    return flask.jsonify({i:partners[idp][i] for i in partners[idp] if i != 'data'})


@app.route('/api/partners/<int:idp>/cashback', methods = ['PUT'])
def addCashback(idp):
    """Реализация Put (новый кэшбек)"""
    try:
        date = datetime.datetime.strptime(request.json['date'], '%Y-%m-%d %H:%M:%S')
    except:
        date = datetime.datetime.strptime(request.json['date'], '%Y-%m-%d')
    if date < partners[idp]['datestop']:
        partners[idp]['spent_budget'] += request.json['cashback']
        partners[idp]['data'].loc[len(partners[idp]['data'])] = [idp, request.json['cashback'], date]
        partners[idp]['is_stopped'] = off(idp)
        if partners[idp]['is_stopped'] and partners[idp]['datestop'] > datetime.datetime(8998, 1, 1):
            partners[idp]['datestop'] = date + datetime.timedelta(days=5)
    return ''

def off(idp):
    """Проверка на остановку акции у партнера"""
    need = partners[idp]['budget'] - partners[idp]['spent_budget']  #сколько есть бюджета у партнера
    if (not len(partners[idp]['data'])) or need > partners[idp]['data'].loc[len(partners[idp]['data']) - 1].cashback * 20: return False
    pred = model_predict(partners[idp]['data'])  #какая сумма кэшбеков предположительно будет
    #print(need, pred, list(partners[idp]['data'].cashback))
    return pred >= need * 1.2 or need < 0  #если предположительная сумма превосходит имеющуюся, то останавливаем (берём с запасом)

def model_predict(data):
    extraction_settings = ComprehensiveFCParameters()

    X = extract_features(data, column_id='id', column_sort='date', column_value='cashback',
                     default_fc_parameters=extraction_settings,
                     # we impute = remove all NaN features automatically
                     impute_function=impute)
    X = X[[
        'cashback__kurtosis',
        'cashback__mean_second_derivative_central',
        'cashback__fft_aggregated__aggtype_"variance"',
        'cashback__agg_autocorrelation__f_agg_"var"__maxlag_40',
        'cashback__fft_aggregated__aggtype_"centroid"',
        'cashback__cid_ce__normalize_True',
        'cashback__cid_ce__normalize_False',
        'cashback__variation_coefficient',
        'cashback__skewness'
    ]]
    return int(model.predict(X)[0])

if __name__ == '__main__':
    with open('model.pkl', 'rb') as inp:
        model = pickle.load(inp)
    port = int(os.environ.get('PORT', 8080))
    app.run(debug = True, host='0.0.0.0', port=port)
