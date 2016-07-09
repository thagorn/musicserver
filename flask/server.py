#!/usr/bin/env python

from flask import Flask, render_template, request, url_for, redirect
from flask_socketio import SocketIO, emit
from pianobarController import PianobarController
from podcastController import PodcastController
from radioController import RadioController
from subprocess import check_output, call
import logging
import sys
import os
import urllib
import requests
import secrets as SECRETS

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

NPR_COOKIE_NAME='RMNPR'
NPR_STATE_NEED_AUTH=0
NPR_STATE_NEED_TOKEN=1
NPR_STATE_AUTHORIZED=2

# replace w/flask session support
SESSION={}

SCHEME_AND_HOST = 'http://rasp-music'
@app.route("/nprOne")
def nprOne():
  # see nprOne/flow.txt
  appCookie = request.cookies.get(NPR_COOKIE_NAME)
  state=parseAppCookie(appCookie)
  if(state == NPR_STATE_NEED_AUTH):
    # 1. no cookie - set cookie, RM=state:AUTH; (can you do that? seems like yes, modulo browser bugs) and redirect to auth, include state=<csrf-token>
    # https://api.npr.org/authorization/v2/authorize?client_id=%(client_id)s&redirect_uri=http%3A%2F%2Frasp-music%2FnprOne&response_type=code&scope=identity.readonly%20identity.write%20listening.readonly%20listening.write&state=abc123
    params={
      'client_id': SECRETS.clientId,
      'redirect_uri': urllib.quote(SCHEME_AND_HOST + url_for('nprOne'),''),
      'scopes': urllib.quote('identity.readonly identity.write listening.readonly listening.write localactivation',''),
      'csrfToken': urllib.quote(generateCsrf(request, SECRETS.csrfKey))
    }
    
    location='https://api.npr.org/authorization/v2/authorize?client_id=%(client_id)s&redirect_uri=%(redirect_uri)s&response_type=code&scope=%(scopes)s&state=%(csrfToken)s' % params
    return redirect(location, code=302)
  if(state == NPR_STATE_NEED_TOKEN):
    #curl -X POST --header 'Content-Type: application/x-www-form-urlencoded' \
    #  --header 'Accept: application/json' \
    #  -d 'grant_type=authorization_code&client_id=%(client_id)s&client_secret=%(client_secret)s&code=%(code)s&redirect_uri=http%3A%2F%2Frasp-music%2FnprOne' \
    #  'https://api.npr.org/authorization/v2/token'
    params={
      'grant_type':    'authorization_code',
      'client_id' :    SECRETS.clientId,
      'client_secret': SECRETS.clientSecret,
      'redirect_uri':  SCHEME_AND_HOST + url_for('nprOne'),
      'code':          request.args.get('code'),
    }
    # doesn't work. complains about grant_type, but I think it only support  form urlencoded, not json
    #tokenResp = requests.post('https://api.npr.org/authorization/v2/token', json=params, headers = {'Accept': 'application/json'})
    # works:
    tokenResp = requests.post('https://api.npr.org/authorization/v2/token', data=params, headers = {'Accept': 'application/json'})
    if(tokenResp.status_code != 200):
      outParams = { 'status': tokenResp.status_code, 'body': tokenResp.text , 'reqHeaders': str(tokenResp.request.headers), 'reqBody': tokenResp.request.body }
      return 'requested token, status = %(status)d, body = %(body)s requestHeaders = %(reqHeaders)s requestBody = %(reqBody)s' % outParams

    # store our token
    json = tokenResp.json()
    accessToken = json.get('token_type') + ' ' + json.get('access_token')
    SESSION['access_token'] = accessToken

    # now get recommendations
    headers = {
      'Authorization': accessToken,
      'Accept':        'application/json',
      'X-Advertising-ID': SECRETS.advertisingId,
    }
    recoResp = requests.get('https://api.npr.org/listening/v2/recommendations?channel=npr', headers = headers)
    outParams = { 'status': recoResp.status_code, 'body': recoResp.text , 'reqHeaders': str(recoResp.request.headers), 'reqBody': recoResp.request.body }
    return 'recommendations: (status = %(status)d)<br/>%(body)s' % outParams
    

def parseAppCookie(cookie):
  # TODO implement for reals
  if(request.args.get('code')):
    return NPR_STATE_NEED_TOKEN
  return NPR_STATE_NEED_AUTH

def generateCsrf(request, key):
  # TODO implement for reals
  return 'abc123'

@app.route("/admin")
def admin():
   return render_template("admin.html")

def broadcast_admin(action, data):
    socketio.emit(action, data, namespace="/adminsocket")

# message: action
#     restart - restart server
@socketio.on("message", namespace="/adminsocket")
def admin_message(message):
   action=message["data"]
   logging.debug("/admin, action is " + str(action))
   if(action == 'restart'):
     logging.warn("Restarting server")
     try:
       with open(os.devnull,'r') as devNull:
         output="/tmp/restart.out"
         result=call(['( sleep 1;../scripts/musicserver >' + output + ' 2>&1 ) &'], shell=True, stdin=devNull, close_fds=True)
     except:
       result="Exception: " + str(sys.exc_info())
   logging.debug("admin result" + str(result))
   broadcast_admin("adminResult", {"result":"restarting server - " + str(result)})
   return "OK"

if __name__ == '__main__':
    FORMAT = '%(asctime)-15s %(clientip)s %(user)-8s %(message)s'
    logging.basicConfig(format=FORMAT)
    logging.info('starting server')
    # disable flash policy server
    socketio.run(app, port=PORT, host=HOST, policy_server=False)
    broadcast_admin("adminResult", {"result":"server restarted"})
