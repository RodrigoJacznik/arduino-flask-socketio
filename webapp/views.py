from __future__ import print_function, division, unicode_literals


from datetime import datetime
import time
import random
import serial
from threading import Thread

from webapp import app, db, socketio
from flask import render_template, redirect, url_for, json
from models import DataType, Data
from forms import HistoricoForm

thread = None


class ArduinoMock():

    def readline(self):
        return ','.join(str(random.random() * 10) for _ in range(3))


class Arduino():
    def __init__(self, fd, baudios):
        self.connection = serial.Serial(fd, baudios)

    def readline(self):
        return self.connection.readline()


def background_thread():
    serial = Arduino('/dev/ttyACM0', 9600)

    temp = DataType.get_or_create('Temperatura', 'float')
    hume = DataType.get_or_create('Humedad', 'int')
    pre = DataType.get_or_create('Presion', 'int')

    while True:
        data = serial.readline().strip()
        tm = datetime.now()
        if (data and data != 'fail'):
            data = data.split(',')
            captura = {'time': tm, 'temperatura': data[0], 'humedad': data[1],
                            'presion': data[2]}
            socketio.emit('EMA data', captura, namespace='/test')

            temp.data.append(Data(timestamp=tm, value=data[0]))
            hume.data.append(Data(timestamp=tm, value=data[1]))
            pre.data.append(Data(timestamp=tm, value=data[2]))
            temp.save()
            hume.save()
            pre.save()

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
        print(form.tm_fin.data, form.tm_inicio.data)
        url = url_for('historico_consulta', tm_inicio=form.tm_inicio.data,
                tm_fin=form.tm_fin.data)
        return redirect(url)
    return render_template('historico_consulta.html', form=form)


@app.route('/historico/<float:tm_inicio>/<float:tm_fin>')
def historico_consulta(tm_inicio, tm_fin):
    print(tm_inicio, tm_fin)
    tm_inicio = datetime.fromtimestamp(tm_inicio)
    tm_fin = datetime.fromtimestamp(tm_fin)

    print(tm_inicio, tm_fin)
    temp = DataType.query_interval('Temperatura', tm_inicio, tm_fin)
    pre = DataType.query_interval('Presion', tm_inicio, tm_fin)
    hume = DataType.query_interval('Humedad', tm_inicio, tm_fin)

    if temp is None or pre is None or hume is None:
        return redirect('historico')
    return render_template('historico.html', temp=temp, hume=hume, pre=pre)



@socketio.on('connect', namespace='/test')
def test_connect():
    print('Client connect')


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')

