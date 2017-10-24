#!/usr/bin/env python
import sys
import logging
import psycopg2
import subprocess
import os

class FileCache:
  def __init__(self, connParams, cacheRoot):
    self.connParams = connParams
    self.cacheRoot = cacheRoot
    self._getCacheMeta()

  def getUrl(self, url):
    if url in self.cache:
      logging.info('TODO: update db on access')
      return self.cache[url]
    else:
      return None

  def preFetch(self, url):
    logging.info('checking ' + url)
    if(url in self.cache):
      logging.debug('already cached - TODO check state & attempts')
      return False
    (pathDir,filename) = self._createCacheRecord(url)
    if(not os.access(pathDir, os.W_OK)):
      os.makedirs(pathDir, 0755)
    curlCmd="curl -L -s '{}' >{}/{}".format(url, pathDir,filename)
    logging.info("via: " + curlCmd)
    subprocess.check_call(["bash", "-c", curlCmd])
    logging.info("TODO: update database")
    logging.info("TODO: update in memory cache")
    return True

  def _createCacheRecord(self, url):
    with psycopg2.connect(self.connParams) as conn, conn.cursor() as cursor:
      cursor.execute('INSERT INTO file_cache(url) VALUES (%s) RETURNING id',[url])
      conn.commit()
      id = cursor.fetchone()[0]
      idStr='{:08x}'.format(id)
      pathDir='{}/{}/{}'.format(idStr[0:2], idStr[2:4], idStr[4:6])
      filename=idStr[6:8]
      path = pathDir + '/' + filename
      cursor.execute('UPDATE file_cache set path = %s where id = %s',[path, id])
      conn.commit()
    return ('{}/{}'.format(self.cacheRoot, pathDir), filename)

  def _getCacheMeta(self):
    # keys are urls
    self.cache = {}
    with psycopg2.connect(self.connParams) as conn, conn.cursor() as cursor:
      cursor.execute('select url, state, size, last_read, attempts, path from file_cache')
      metaData = cursor.fetchone()
      while metaData:
        self.cache[metaData[0]] = {
          'url': metaData[0],
	  'state': metaData[1],
	  'size': metaData[2],
	  'last_read': metaData[3],
	  'attempts': metaData[4],
	  'path': self.cacheRoot + '/' + metaData[5]
	}
        metaData = cursor.fetchone()

