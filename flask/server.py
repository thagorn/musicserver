#!/usr/bin/env python

from flask import Flask, render_template, request
from flask.ext.socketio import SocketIO, emit
from pianobarController import PianobarController
import logging

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super secry'
socketio = SocketIO(app)
PORT = 80
HOST = '0.0.0.0'
PCONTROLLER = None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/pandora/")
def pandora():
    global PCONTROLLER
    if not PCONTROLLER:
        PCONTROLLER = PianobarController()
    else:
        PCONTROLLER.check_status()
    return render_template("pandora.html",
                data=PCONTROLLER.get_latest(),
                paused=PCONTROLLER.is_paused(),
                time=PCONTROLLER.get_time(),
                volume=PCONTROLLER.get_volume())

@socketio.on("volume", namespace="/pandorasocket")
def pandora_volume(volume):
    PCONTROLLER.set_volume(int(volume["data"]))
    broadcast_pandora("volumechanged", {"volume":PCONTROLLER.get_volume()})

@socketio.on("message", namespace="/pandorasocket")
def pandora_message(message):
    data = message["data"]
    PCONTROLLER.write(message["data"])
    if data == "p":
        PCONTROLLER.pause()
        broadcast_pandora("onpause", {"paused":PCONTROLLER.is_paused()})
    if PCONTROLLER.is_paused() and data[0:1] == "s":
        PCONTROLLER.pause()
        broadcast_pandora("onpause", {"paused":PCONTROLLER.is_paused()})
    return "OK"

@app.route("/pianobar/<action>", methods=["POST"])
def pianobar_message(action):
    data = request.json
    PCONTROLLER.set_latest(action, data)
    broadcast_pandora(action, data)
    return "OK"

def broadcast_pandora(action, data):
    socketio.emit(action, data, namespace="/pandorasocket")


if __name__ == '__main__':
    socketio.run(app, port=PORT, host=HOST)
