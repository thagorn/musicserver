from string import split
from urllib2 import urlopen
from mediaplayerController import get_mediaplayer
import xml.etree.ElementTree as ET
import time

class PodcastController():
    def __init__(self):
        self.dir = '/home/pi/podcast/data/'
        self.feeds = self.dir + 'feeds.txt'
        self.paused = True
        self.elapsedTime = 0
        self.startTime = time.time()

    def get_feeds(self):
        with open(self.feeds) as input:
           feedData = input.readlines()
        return map(lambda x: split(x,'|'), feedData)

    def get_feed(self, url):
        try:
            namespaces = {'itunes':'http://www.itunes.com/dtds/podcast-1.0.dtd'}
            feedData = urlopen(url)
            channel = ET.parse(feedData).getroot().find('channel')
            feed = dict()
            feed['title'] = channel.find("title").text
            feed['image'] = channel.find("image").find("url").text
            feed['items'] = []
            for item in channel.findall("item"):
                feedItem = dict()
                feedItem['title'] = item.find('title').text
                duration = item.find('itunes:duration',namespaces).text
                feedItem['duration'] = duration
                parts = duration.split(':')
                feedItem['durationSecs'] = int(parts[0]) * 60 + int(parts[1])
                feedItem['guid'] = item.find('guid').text
                feed['items'].append(feedItem)
        finally:
            feedData.close()
        return feed

    def play_podcast(self, url, duration, durationSecs, title):
        mp = get_mediaplayer()
        mp.play(url)
        self.paused = False
        self.elapsedTime = 0
        self.startTime = time.time()
        return { 'duration': duration,
                 'durationSecs': durationSecs,
                 'title': title }

    def pause(self):
        self.write('pause')
        self.paused = not self.paused
        if self.paused:
            self.elapsedTime = self.elapsedTime + time.time() - self.startTime
        else:
            self.startTime = time.time()

    def is_paused(self):
        return self.paused

    def get_time(self):
        if self.paused:
            return self.elapsedTime
        else:
            return self.elapsedTime + time.time() - self.startTime

    # write straight to mplayer fifo
    def write(self, message):
        get_mediaplayer().write(message)
                
           
    
