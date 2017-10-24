#!/usr/bin/env python
import logging
FORMAT = '%(asctime)-15s:%(name)s:%(levelname)s:%(message)s:%(funcName)s:%(module)s:%(lineno)d'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
import sys
# inject this!
sys.path.append('/home/pi/musicserver/flask')
from podcastController import PodcastController as PC
from file_cache import FileCache

def stop():
  sys.exit(0)

def main():
  # inject these too!
  connParams='dbname=pi user=pi'
  cacheRoot='/data/musicserver/cache'
  maxToFetch=20

  pc = PC()
  cache = FileCache(connParams, cacheRoot)
  count = 0
  for feed in pc.get_feeds():
    logging.info('Checking ' + feed[0])
    for item in pc.get_feed(feed[1])['items']:
      if(cache.preFetch(item['guid'])):
        count = count + 1
        logging.debug('count now ' + str(count))
        if(count >= maxToFetch):
          logging.info('fetched ' + str(maxToFetch) + ' item(s) - stopping')
          stop()
  stop()


if __name__ == '__main__':
  main()
