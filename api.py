from flask import request
import flask, sqlite3

app = flask.Flask(__name__, static_url_path = "")
partners = []

def addPartnerBD(partner):
    cur.execute(f'INSERT INTO Partners VALUES ({partner['id']}, "{partner['name']}", {partner['budget']}, 0, false)')

def addPartner(partner):
    '''если мы не используем bd'''
    partners.append(partner)

def foundPartnerBD(id):
    cur.execute(f'SELECT * FROM Partners WHERE id = {id}')
    data = cur.fetchall()[0]
    return dict(zip(['id', 'name', 'budget', 'spent_budget', 'is_stopped'], data))

def foundPartner(id):
    '''если мы не используем bd'''
    return partners[id]

def updatePartnerBD(id, text):
    cur.execute(f'UPDATE Partners SET {text} WHERE id = {id}')

def updateCache(id, v):
    partners[id]['spent_budget'] = v

def updateStopped(id):
    partners[id]['is_stopped'] = True

@app.route('/')
def main():
    '''Переадресация на красивую картинку'''
    return flask.send_from_directory(".", path="index.html")

@app.route('/api/partners/<int:id>', methods = ['GET'])
def getPartner(id):
    '''Реализация Get (информация о партнёре)'''
    return flask.jsonify(foundPartnerBD(id))

@app.route('/api/partners', methods = ['POST'])
def createPartner():
    '''Реализация Post (новый партнёр)'''
    global countPartners
    partner = {
        'id': countPartners,
        'name': request.json['name'],
        'budget': request.json['budget'],
        'spent_budget': 0
        #'is_stopped': False
    }
    countPartners += 1
    addPartnerBD(partner)
    return flask.jsonify(partner), 201

@app.route('/api/partners/<int:id>', methods = ['PUT'])
def addCashback(id):
    '''Реализация Put (новый кэшбек)'''
    partner = foundPartnerBD(id)
    updatePartnerBD(id, f"spent_budget = {partner['spent_budget'] + request.json['cashback']}")
    """
    Здесь отправка данных в нейронку и проверка на остановку акций партнера.
    """
    return ''

if __name__ == '__main__':
    conn = sqlite3.connect('db.db', check_same_thread=False)
    countPartners = 0
    cur = conn.cursor()
    cur.execute('''DROP TABLE IF EXISTS Partners''')
    cur.execute('''
    CREATE TABLE Partners (
    id INTEGER PRIMARY KEY,
    name TEXT,
    budget INTEGER,
    spent_budget INTEGER,
    is_stopped BOOLEAN
    )''') #пересоздаём таблицу
    app.run(debug = False, port=8080)
    conn.close()
