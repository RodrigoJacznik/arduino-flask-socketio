from __future__ import print_function, division, unicode_literals

from consumer import *
from socket_wrapp import Socket
from protocol import *

from gevent import monkey
monkey.patch_all()

import time
import random
import serial
from threading import Thread

from pymongo import MongoClient
from flask import Flask, render_template, redirect, url_for, jsonify
from flask.ext.socketio import SocketIO, emit

from forms import HistoricoForm

client = MongoClient()
db = client['EMA']

app = Flask(__name__)
app.config.from_object('config')
app.debug = True
socketio = SocketIO(app)
thread = None
cons=Consumidor(Socket()) #consumidor global. Un solo connect en fuentesDS!por lo tanto entrar siempreprimero a /fuenteds!!

class ArduinoMock():

    def readline(self):
        return ','.join(str(random.random() * 10) for _ in range(3))


class Arduino():
    def __init__(slef, fd, baudios):
        self.connection = serial.Serial(fd, baudios)

    def readline(self):
        return self.connection.readline()



def background_thread():
    serial = ArduinoMock()

    while True:
        data = serial.readline().strip()
       
        tm = time.time()
        if (data and data != 'fail'):
            data = data.split(',')
            captura = {'time': tm, 'temperatura': data[0], 'humedad': data[1],
                            'presion': data[2]}
            socketio.emit('EMA data', captura, namespace='/test')
            db.captura_EMA.insert(captura)
        time.sleep(2)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/realtime')
def realtime():
    global thread
    if thread is None:
        thread = Thread(target=background_thread)
        thread.start()
    return render_template('realtime.html')

@app.route('/historico', methods=['GET', 'POST'])
def historico():
    form = HistoricoForm()
    if form.validate_on_submit():
        url = url_for('historico_consulta', tm_inicio=str(form.tm_inicio.data),
                tm_fin=str(form.tm_fin.data))
        return redirect(url)
    return render_template('historico_consulta.html', form=form)


@app.route('/historico/<float:tm_inicio>/<float:tm_fin>')
def historico_consulta(tm_inicio, tm_fin):
    data = {"data": list(db.captura_EMA.find({'$and': [{'time': {'$gte': tm_inicio}},
        {'time': {'$lte': tm_fin}}]}, {'_id': 0}))}
    
    t = {"tm": [], "data": []}
    p = {"tm": [], "data": []}
    h = {"tm": [], "data": []}

    for d in data['data']:
        t['tm'].append(d['time'])
        p['tm'].append(d['time'])
        p['tm'].append(d['time'])
 
        t['data'].append(d['temperatura'])
        p['data'].append(d['presion'])
        h['data'].append(d['humedad'])

    return render_template('historico.html', data=data)

@app.route('/fuentesds')
def fuentesDS():
    
   # cons = Consumidor(Socket())
    cons.connect_server("127.0.0.1",8888)
    sources2=[]  
    sources = [" ".join(data.split(',')) for data in cons.request_sources()]
    
    return render_template('fuentesds.html',fuentes=sources,cantidad=len(sources))

@app.route('/fuentesds/<idFuente>')
def fuentesds_id(idFuente):
    print(idFuente)
    datos=[]
   
    if (cons.select_source(idFuente)):
        for dato in cons.start_stream(GET_OP_NORMAL,1):
            datos.append(dato)
            print (dato)

        return render_template('rtds.html',id =idFuente,datos=datos)
    else:
        return ("FUENTE INEXISTENTE") #Crear Pagina de ERROR


@socketio.on('connect', namespace='/test')
def test_connect():
    print('Client connect')


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')


if __name__ == '__main__':
    socketio.run(app)

