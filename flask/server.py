#!/usr/bin/env python

from flask import Flask, render_template, request
from flask.ext.socketio import SocketIO, emit
from pianobarController import PianobarController
from podcastController import PodcastController
from radioController import RadioController
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
    logging.debug("pianobar_message - action: {0} data: {1}".format(action, data))
    PCONTROLLER.set_latest(action, data)
    broadcast_pandora(action, data)
    return "OK"

def broadcast_pandora(action, data):
    socketio.emit(action, data, namespace="/pandorasocket")

PODCAST = None

def getPodcast():
    global PODCAST
    if not PODCAST:
        PODCAST = PodcastController()
    return PODCAST
    
@app.route("/podcast/")
def podcast():
    return render_template("podcast.html",
        feeds=getPodcast().get_feeds())

@app.route("/podcast/feed/<path:url>")
def podcast_feed(url):
    return render_template("podcast_feed.html",
        podcasts=getPodcast().get_feed(url))

@app.route("/podcast/play/<path:url>")
def podcast_play(url):
    return render_template("podcast_play.html",
        podcast=getPodcast().play_podcast(url,request.args.get('duration'), request.args.get('durationSecs'), request.args.get('title')),
        paused=False,
        time=getPodcast().get_time())

def broadcast_podcast(action, data):
    socketio.emit(action, data, namespace="/podcastsocket")

@socketio.on("message", namespace="/podcastsocket")
def podcast_message(message):
    data = message["data"].split('|')
    if data[0] == 'mp':
       getPodcast().write(data[1])
    elif data[0] == 'ct':
       if data[1] == 'next':
         getPodcast().playNext()
       elif data[1] == 'pause':
         getPodcast().pause()
         broadcast_podcast("onpause", {"paused":getPodcast().is_paused()})
       elif data[1] == 'swap':
         getPodcast().swap(data[2], data[3])
       else:
         logging.warn('Unknown podcastsocket message: ' + message)
    else:
      logging.warn('Unknown podcastsocket message: ' + message)
    return "OK"


RADIO = None

def getRadio():
    global RADIO
    if not RADIO:
        RADIO = RadioController()
    return RADIO

@app.route("/radio/")
def radio():
    radio = getRadio()
    return render_template("radio.html",
                data=radio.get_latest(),
                paused=radio.is_paused(),
                time=radio.get_time(),
                volume=radio.get_volume())

def broadcast_radio(action, data):
    socketio.emit(action, data, namespace="/radiosocket")

@socketio.on("message", namespace="/radiosocket")
def radio_message(message):
    data = message["data"].split('|')
    if data[0] == 's':
       getRadio().play(data[1],data[2])
    elif data[0] == 'pause':
       getRadio().pause()
       broadcast_radio("onpause", {"paused":getRadio().is_paused()})
    else:
         logging.warn('Unknown radiosocket message: ' + mesage)
    return "OK"

if __name__ == '__main__':
    socketio.run(app, port=PORT, host=HOST)
