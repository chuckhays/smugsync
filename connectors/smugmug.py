import datetime
import os
from connectorbase import ConnectorBase
from file import File, FileEncoder
import sys
import json
import time

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

class SmugMugConnector(ConnectorBase):

  def __init__(self, config_data):
    super(SmugMugConnector, self).__init__(config_data)
    self.api_key = config_data.get(API_KEY_KEY)
    self.oauth_secret = config_data.get(OAUTH_SECRET_KEY)
    self.app_name = config_data.get(APP_NAME_KEY)
    self.access_token = None
    self.cache = None

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

  def enumerate_objects(self):
    images = {}
    # Find authed user.
    authUser = self.session.get(API_ORIGIN + '/api/v2!authuser', headers={'Accept': 'application/json'}).json()
    userAlbumsUri = self.get_json_key(authUser,['Response', 'User', 'Uris', 'UserAlbums', 'Uri'])
    if userAlbumsUri is None:
      print 'Could not find URI for user\'s albums'
      return images
    # Request all albums.
    userAlbums = self.session.get(API_ORIGIN + userAlbumsUri,params = {'count':'1000000', 'expand':'AlbumImages'}, headers={'Accept': 'application/json'}).json()

    albumsArray = self.get_json_key(userAlbums, ['Response', 'Album'])
    if albumsArray is None:
      print 'Could not find list of albums for user'
      return images

    for album in progress.bar(albumsArray):
      # If an album is in the cache, and the last updated timestamp matches, we can use the cached value.
      #albumUri = self.get_json_key(album, ['Uri'])
      albumLastUpdatedString = self.get_json_key(album, ['ImagesLastUpdated'])
      albumUri = self.get_json_key(album, ['Uris', 'AlbumImages', 'Uri'])
      cachedImages = self.check_cache(albumUri, albumLastUpdatedString)
      if cachedImages is not None:
        for image in images:
          self.add_file_to_hash(image, images)
        continue
      if albumUri is None:
        print 'Could not find album images Uri for album: ' + self.get_json_key(album, ['Name'])
        continue
      #start_time = time.time()
      albumImages = self.session.get(API_ORIGIN + albumUri, params = {'count':'1000000'}, headers={'Accept': 'application/json'}).json()
      #elapsed_time = time.time() - start_time
      #time_from_json = self.get_json_key(albumImages, ['Response', 'Timing', 'Total', 'time'])
      #if time_from_json is None:
      #  time_from_json = 0.0
      #print 'elapsed time: %f total time: %f ' % (elapsed_time, time_from_json)
      imagesArray = self.get_json_key(albumImages, ['Response', 'AlbumImage'])
      if imagesArray is None:
        print 'Could not get images array for album: ' + self.get_json_key(album, ['Name']) + 'uri:' + albumUri
        continue
      albumImages = []
      for image in imagesArray:
        file = File()
        file.name = self.get_json_key(image, ['FileName'])
        file.relativePath = os.path.normpath(self.get_json_key(album, ['UrlPath']))
        file.originalPath = os.path.normpath(os.path.join(file.relativePath, file.name))
        file.size = self.get_json_key(image, ['ArchivedSize'])

        _, fileExtension = os.path.splitext(file.name)
        file.type = File.type_from_extension(fileExtension)
        albumImages.append(file)
        self.add_file_to_hash(file, images)
      self.put_cache(albumUri, albumLastUpdatedString, album, albumImages)
     
    return images

  def check_cache(self, album_uri, album_last_updated_string):

    self.init_cache()
    if not album_uri in self.cache:
      return None
    data = self.cache[album_uri]
    album_last_updated = datetime.datetime.now()
    if album_last_updated_string is not None:
      album_last_updated = parser.parse(album_last_updated_string)
    cached_album_last_updated_string = self.get_json_key(data, ['lastupdated'])
    cached_album_last_updated = datetime.datetime.fromtimestamp(0)
    if cached_album_last_updated_string is not None:
      cached_album_last_updated = parser.parse(cached_album_last_updated_string)
    if not isinstance(cached_album_last_updated, datetime.datetime):
      return None
    if not isinstance(album_last_updated, datetime.datetime):
      return None
    if cached_album_last_updated < album_last_updated:
      return None
    return self.get_json_key(data, ['images'])

  def put_cache(self, album_uri, album_last_updated_string, album, images):
    data = {
      'lastupdated' : album_last_updated_string,
      'album' : album,
      'images' : images,
    }
    self.cache[album_uri] = data
    self.save_cache()

  def file_from_dict(self, d):
    f = File()
    f.__dict__.update(d)
    return f

  def init_cache(self):
    if self.cache is None:
      try:
        data = {}
        if os.path.exists(CACHE_FILE):
          with open(CACHE_FILE, 'r') as json_data:
            data = json.load(json_data)
        for uri in data:
          v = data[uri]
          images = v['images']
          files = [self.file_from_dict(i) for i in images]
          v['images'] = files
        self.cache = data
      except ValueError:
        print 'Empty or corrupted json cache.'
        self.cache = {}

  def save_cache(self):
    with open(CACHE_FILE, 'w') as json_data:
      json.dump(self.cache, json_data, cls=FileEncoder)
