musicserver
===========

Quick flask based music server for use on a rasberry pi

#Dependencies
apt-get install build-essential libao-dev libmad0-dev libfaad-dev libgnutls-dev libjson0-dev ffmpeg git libgcrypt11-dev yasm make pkg-config
##Install ffmpeg from source
git clone https://github.com/FFmpeg/FFmpeg.git
cd FFmpeg
./configure
### 'make' can take several hours
make clean && make && make install
cd ..
## install pianobar manually from source
git clone https://github.com/PromyLOPh/pianobar.git
cd pianobar
make clean && make && make install
## configure alsa
vim /usr/share/alsa/alsa.conf
### pcm.front cards.pcm.front => pcm.front cards.pcm.default
# Python dependencies
pip install flask flask-socketio requests
# Start server
cd flask
chmod a+x server.py
./server.py
