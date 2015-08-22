import datetime
import os
from connectorbase import ConnectorBase
from file import File
import sys
import json

from rauth import OAuth1Service
from rauth import OAuth1Session
#from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from urlparse import urlsplit, urlunsplit, parse_qsl
from urllib import urlencode

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

class SmugMugConnector(ConnectorBase):

  def __init__(self, config_data):
    super(SmugMugConnector, self).__init__(config_data)
    self.api_key = config_data.get(API_KEY_KEY)
    self.oauth_secret = config_data.get(OAUTH_SECRET_KEY)
    self.app_name = config_data.get(APP_NAME_KEY)
    self.access_token = None

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

  def enumerate_objects(self):
    images = []
    # Find authed user.
    authUser = self.session.get(API_ORIGIN + '/api/v2!authuser', headers={'Accept': 'application/json'}).json()
    userAlbumsUri = authUser['Response']['User']['Uris']['UserAlbums']['Uri']
    # Request all albums.
    userAlbums = self.session.get(API_ORIGIN + userAlbumsUri,params = {'count':'1000000'}, headers={'Accept': 'application/json'}).json()
    albumsArray = userAlbums['Response']['Album']
    for album in albumsArray:
      print 'album: ' + album['Name'] + '(' + album['UrlPath'] + ')'
      albumUri = album['Uris']['AlbumImages']['Uri']
      albumImages = self.session.get(API_ORIGIN + albumUri, params = {'count':'1000000'}, headers={'Accept': 'application/json'}).json()
      imagesArray = albumImages['Response']['AlbumImage']
      for image in imagesArray:
        img = { 'name' : image['FileName'], 'size' : image['ArchivedSize'], 'md5' : image['ArchivedMD5'], 'folder' : album['UrlPath'] }
        images.append(img)
     
    return images
