import datetime
import os
from connectorbase import ConnectorBase
from file import File, FileEncoder
import sys
import json
import time
import threading

import shelve

from rauth import OAuth1Service
from rauth import OAuth1Session
#from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from urlparse import urlsplit, urlunsplit, parse_qsl
from urllib import urlencode

from clint.textui import progress
from dateutil import parser


API_KEY_KEY = "apiKey"
OAUTH_SECRET_KEY = "oauthSecret"
APP_NAME_KEY = "appName"
ACCESS_TOKEN_KEY = "accessToken"
ACCESS_TOKEN_SECRET_KEY = "accessTokenSecret"

OAUTH_ORIGIN = 'https://secure.smugmug.com'
REQUEST_TOKEN_URL = OAUTH_ORIGIN + '/services/oauth/1.0a/getRequestToken'
ACCESS_TOKEN_URL = OAUTH_ORIGIN + '/services/oauth/1.0a/getAccessToken'
AUTHORIZE_URL = OAUTH_ORIGIN + '/services/oauth/1.0a/authorize'

API_ORIGIN = 'http://api.smugmug.com'
BASE_URL = API_ORIGIN + '/api/v2'

CACHE_FILE = 'smugmug.cache'

MAX_THREADS = 10

class SmugMugConnector(ConnectorBase):

  def __init__(self, config_data):
    super(SmugMugConnector, self).__init__(config_data)
    self.api_key = config_data.get(API_KEY_KEY)
    self.oauth_secret = config_data.get(OAUTH_SECRET_KEY)
    self.app_name = config_data.get(APP_NAME_KEY)
    self.access_token = None
    self.cache = None
    self.shelve = None

    self.images = None
    self.bar = None

    self.max_threads_lock = threading.Semaphore(MAX_THREADS)

    self.thread_count = 0
    self.thread_count_lock = threading.Lock()
    self.cache_lock = threading.Lock()
    self.output_lock = threading.Lock()

  def authenticate(self):
    filename = self.data_file
    if not filename:
      filename = "smugmug.data"
    data = {}
    if os.path.exists(filename):
      with open(filename, 'r') as json_data:
        data = json.load(json_data)
    # Check for cached accessToken
    self.access_token = data.get(ACCESS_TOKEN_KEY)
    self.access_token_secret = data.get(ACCESS_TOKEN_SECRET_KEY)
    if not self.access_token or not self.access_token_secret:
      service = OAuth1Service(name=self.app_name, consumer_key=self.api_key, consumer_secret=self.oauth_secret, request_token_url=REQUEST_TOKEN_URL, access_token_url=ACCESS_TOKEN_URL, authorize_url=AUTHORIZE_URL, base_url=BASE_URL)
      rt, rts = service.get_request_token(params={'oauth_callback': 'oob'})
      auth_url = self.add_auth_params(service.get_authorize_url(rt), access='Full', permissions='Modify')
      print('Go to %s in a web browser.' % auth_url)

      sys.stdout.write('Enter the six-digit code: ')
      sys.stdout.flush()
      verifier = sys.stdin.readline().strip()
      at, ats = service.get_access_token(rt, rts, params={'oauth_verifier': verifier})
      print('Access token: %s' % at)
      print('Access token secret: %s' % ats)
      
      self.access_token = at
      self.access_token_secret = ats

      with open(filename, 'w') as json_data:
        json.dump({ ACCESS_TOKEN_KEY : self.access_token, ACCESS_TOKEN_SECRET_KEY : self.access_token_secret }, json_data)
    self.session = OAuth1Session(self.api_key, self.oauth_secret, access_token=self.access_token, access_token_secret=self.access_token_secret)
    #print(self.session.get(API_ORIGIN + '/api/v2!authuser', headers={'Accept': 'application/json'}).json())
    return True

  def add_auth_params(self, auth_url, access=None, permissions=None):
    if access is None and permissions is None:
        return auth_url
    parts = urlsplit(auth_url)
    query = parse_qsl(parts.query, True)
    if access is not None:
        query.append(('Access', access))
    if permissions is not None:
        query.append(('Permissions', permissions))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query, True), parts.fragment))

  def get_json_key(self, json, key_array):
    current = json
    for key in key_array:
      if not key in current:
        return None
      current = current[key]
    return current
  
  def fetch_album_images(self, album):
    with self.max_threads_lock:
      album_last_updated_string = self.get_json_key(album, ['ImagesLastUpdated'])
      album_uri = self.get_json_key(album, ['Uris', 'AlbumImages', 'Uri'])
      # Check cache for album!images results, if not, request from network.
      cached_album_images = None
      with self.cache_lock:
        _, cached_album_images = self.check_cache(album_uri, album_last_updated_string)
      if cached_album_images is None:
        if album_uri is None:
          print 'Could not find album images Uri for album: ' + self.get_json_key(album, ['Name'])
          return
        cached_album_images = self.session.get(API_ORIGIN + album_uri, params = {'count':'1000000'}, headers={'Accept': 'application/json'}).json()
        with self.cache_lock:
          self.put_cache(album_uri, album_last_updated_string, album, cached_album_images)
      images_array = self.get_json_key(cached_album_images, ['Response', 'AlbumImage'])
      if images_array is None:
        print 'Could not get images array for album: ' + self.get_json_key(album, ['Name']) + 'uri:' + album_uri
        return

      for image in images_array:
        file = File()
        file.name = self.get_json_key(image, ['FileName'])
        file.relativePath = os.path.normpath(self.get_json_key(album, ['UrlPath']))
        file.originalPath = os.path.normpath(os.path.join(file.relativePath, file.name))
        file.size = self.get_json_key(image, ['ArchivedSize'])
        _, file_extension = os.path.splitext(file.name)
        file.type = File.type_from_extension(file_extension)
        with self.output_lock:
          self.add_file_to_hash(file, self.images)
      self.increment_threadcount()

  def enumerate_objects(self):
    self.images = {}
    # Find authed user.
    authUser = self.session.get(API_ORIGIN + '/api/v2!authuser', headers={'Accept': 'application/json'}).json()
    userAlbumsUri = self.get_json_key(authUser,['Response', 'User', 'Uris', 'UserAlbums', 'Uri'])
    if userAlbumsUri is None:
      print 'Could not find URI for user\'s albums'
      return self.images
    # Request all albums.
    userAlbums = self.session.get(API_ORIGIN + userAlbumsUri,params = {'count':'1000000', 'expand':'AlbumImages'}, headers={'Accept': 'application/json'}).json()

    albums_array = self.get_json_key(userAlbums, ['Response', 'Album'])
    if albums_array is None:
      print 'Could not find list of albums for user'
      return self.images

    self.bar = progress.Bar(expected_size = len(albums_array))
    threads = []
    for album in albums_array:
      thread = threading.Thread(target=self.fetch_album_images, args=(album,))
      thread.start()
      threads.append(thread)

    for thread in threads:
      thread.join()

    self.shelve.close()
    return self.images

  def increment_threadcount(self):
    with self.thread_count_lock:
      self.thread_count += 1
      self.bar.show(self.thread_count)

  # Check for unexpired cached json results.
  def check_cache(self, album_uri, album_last_updated_string):
    album_uri = str(album_uri)
    self.init_cache()
    if not album_uri in self.shelve:
      return (None, None)
    data = self.shelve[album_uri]
    album_last_updated = datetime.datetime.now()
    if album_last_updated_string is not None:
      album_last_updated = parser.parse(album_last_updated_string)
    cached_album_last_updated_string = self.get_json_key(data, ['lastupdated'])
    cached_album_last_updated = datetime.datetime.fromtimestamp(0)
    if cached_album_last_updated_string is not None:
      cached_album_last_updated = parser.parse(cached_album_last_updated_string)
    if not isinstance(cached_album_last_updated, datetime.datetime):
      return (None, None)
    if not isinstance(album_last_updated, datetime.datetime):
      return (None, None)
    if cached_album_last_updated < album_last_updated:
      return (None, None)
    return (self.get_json_key(data, ['album']), self.get_json_key(data, ['images']))

  def put_cache(self, album_uri, album_last_updated_string, album, images):
    album_uri = str(album_uri)
    data = {
      'lastupdated' : album_last_updated_string,
      'album' : album,
      'images' : images,
    }
    self.shelve[album_uri] = data
    self.save_cache()

  def init_cache(self):
    if self.shelve is None:
      self.shelve = shelve.open(CACHE_FILE, writeback = True)

  def save_cache(self):
    self.shelve.sync()
