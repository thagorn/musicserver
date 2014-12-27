from string import split
from urllib2 import urlopen
from mediaplayerController import get_mediaplayer
import xml.etree.ElementTree as ET

class PodcastController():
    def __init__(self):
        self.dir = '/home/pi/podcast/data/'
        self.feeds = self.dir + 'feeds.txt'

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
                feedItem['duration'] = item.find('itunes:duration',namespaces).text
                feedItem['guid'] = item.find('guid').text
                feed['items'].append(feedItem)
        finally:
            feedData.close()
        return feed

    def play_podcast(self, url, duration, title):
        mp = get_mediaplayer()
        mp.play(url)
        return { 'duration': duration,
                 'title': title }
                
                
           
    
