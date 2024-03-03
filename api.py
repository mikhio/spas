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

@app.route('/api/partners', methods = ['GET', 'POST'])
def createPartner():
    """Реализация Post (новый партнёр)"""
    if request.method == 'POST':
        partner = {
            'id': len(partners),
            'name': request.json['name'],
            'budget': float(request.json['budget']),
            'spent_budget': 0,
            'is_stopped': False,
            'data': pd.DataFrame({'id': pd.Series(dtype='int'),
                       'cashback': pd.Series(dtype='int'),
                       'date': pd.Series(dtype='datetime64[ns]')}),
            'datestop': datetime.datetime(8999, 1, 1)
        }
        partners.append(partner)
        return flask.jsonify({i:partner[i] for i in partner if i not in ['data', 'is_stopped']}), 201
    else:
        new_data = []
        for p in partners:
            new_partner = p.copy()
            new_partner['data'] = p['data'].to_dict('records')
            # print(p['data'].to_dict('records'))  
            new_data.append(new_partner)

        return flask.jsonify({'partners': new_data}), 201 


@app.route('/api/partners/<int:idp>', methods = ['GET'])
def getPartner(idp):
    """Реализация Get (информация о партнёре)"""
    if len(partners) <= idp:
        return 'Not Found', 404
    #print(partners[idp]['is_stopped'])
    if not partners[idp]['is_stopped']:
        partners[idp]['is_stopped'] = off(idp)

    new_partner = partners[idp].copy()
    new_partner['data'] = new_partner['data'].to_dict('records')
    return flask.jsonify(new_partner), 200



@app.route('/api/partners/<int:idp>/cashback', methods = ['PUT'])
def addCashback(idp):
    """Реализация Put (новый кэшбек)"""
    try:
        date = datetime.datetime.strptime(request.json['date'], '%Y-%m-%d %H:%M:%S')
    except:
        date = datetime.datetime.strptime(request.json['date'], '%Y-%m-%d')
    cashback = int(request.json['cashback'])
    if date < partners[idp]['datestop']:
        partners[idp]['spent_budget'] += cashback
        partners[idp]['data'].loc[len(partners[idp]['data'])] = [idp, cashback, date]
        print(partners[idp]['data'])
        if not partners[idp]['is_stopped']:
            partners[idp]['is_stopped'] = off(idp)
        if partners[idp]['is_stopped'] and partners[idp]['datestop'] > datetime.datetime(8998, 1, 1):
            partners[idp]['datestop'] = date + datetime.timedelta(days=5)

    new_partner = partners[idp].copy()
    new_partner['data'] = new_partner['data'].to_dict('records')
    return flask.jsonify(new_partner), 200

def off(idp):
    """Проверка на остановку акции у партнера"""
    need = partners[idp]['budget'] - partners[idp]['spent_budget']  #сколько есть бюджета у партнера

    #условия выхода
    if need <= 0: return True #если мы уже опаздали
    if len(partners[idp]['data']) < 5: return False #если данных недостаточно
    # if len(partners[idp]['data']) and need < partners[idp]['data'].loc[len(partners[idp]['data']) - 1].cashback * 2:
    #     return True #если бюджета осталось прям супер мало
    # if len(partners[idp]['data']) and need > partners[idp]['data'].loc[len(partners[idp]['data']) - 1].cashback * 20:
    #     return False #если бюджета предостаточно
    # if len(partners[idp]['data']) and need < sum([partners[idp]['data'].loc[i].cashback for i in list(partners[idp]['data'].index)[-5:]]):
    #     return True
    pred = model_predict(partners[idp]['data'])  #какая сумма кэшбеков предположительно будет
    print(need, pred, partners[idp]['is_stopped'])
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
    with open('models/model_2.0.pkl', 'rb') as inp:
        model = pickle.load(inp)
    port = int(os.environ.get('PORT', 8080))
    app.run(debug = True, host='0.0.0.0', port=port)
