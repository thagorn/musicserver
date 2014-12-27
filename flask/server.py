#!/usr/bin/env python

from flask import Flask, render_template, request
from flask.ext.socketio import SocketIO, emit
from pianobarController import PianobarController
from podcastController import PodcastController
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
        podcast=getPodcast().play_podcast(url,request.args.get('duration'), request.args.get('title')))

if __name__ == '__main__':
    socketio.run(app, port=PORT, host=HOST)
