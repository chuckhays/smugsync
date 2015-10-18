import json
import os
import sys
from urlparse import urlsplit, urlunsplit, parse_qsl
from urllib import urlencode

from rauth import OAuth1Service
from rauth import OAuth1Session

ACCESS_TOKEN_KEY = "accessToken"
ACCESS_TOKEN_SECRET_KEY = "accessTokenSecret"

OAUTH_ORIGIN = 'https://secure.smugmug.com'
REQUEST_TOKEN_URL = OAUTH_ORIGIN + '/services/oauth/1.0a/getRequestToken'
ACCESS_TOKEN_URL = OAUTH_ORIGIN + '/services/oauth/1.0a/getAccessToken'
AUTHORIZE_URL = OAUTH_ORIGIN + '/services/oauth/1.0a/authorize'

API_ORIGIN = 'http://api.smugmug.com'
BASE_URL = API_ORIGIN + '/api/v2'


class Smugmug(object):
    def __init__(self, api_key=None, oauth_secret=None, app_name=None, access_cache_file='smugmug.access'):
        self.api_key = api_key
        self.oauth_secret = oauth_secret
        self.app_name = app_name
        self.access_token = None
        self.access_token_secret = None
        self.access_cache_file = access_cache_file
        self.session = None

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

    def authenticate(self):
        data = {}
        if os.path.exists(self.access_cache_file):
            with open(self.access_cache_file, 'r') as json_data:
                data = json.load(json_data)
        # Check for cached accessToken
        self.access_token = data.get(ACCESS_TOKEN_KEY)
        self.access_token_secret = data.get(ACCESS_TOKEN_SECRET_KEY)
        if not self.access_token or not self.access_token_secret:
            service = OAuth1Service(name=self.app_name, consumer_key=self.api_key, consumer_secret=self.oauth_secret,
                                    request_token_url=REQUEST_TOKEN_URL, access_token_url=ACCESS_TOKEN_URL,
                                    authorize_url=AUTHORIZE_URL, base_url=BASE_URL)
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
            # Cache access token and access token secret so we don't have to authenticate on the next run.
            with open(self.access_cache_file, 'w') as json_data:
                json.dump({ACCESS_TOKEN_KEY: self.access_token, ACCESS_TOKEN_SECRET_KEY: self.access_token_secret},
                          json_data)
        self.session = OAuth1Session(self.api_key, self.oauth_secret, access_token=self.access_token,
                                     access_token_secret=self.access_token_secret)

    def get_authorized_user(self):
        auth_user_response = self.session.get(API_ORIGIN + '/api/v2!authuser',
                                              headers={'Accept': 'application/json'}).json()
        authed_user = self.get_json_key(auth_user_response, ['Response', 'User', 'Name'])
        return authed_user

    def get_albums(self, user, include_images=False):
        user_response = self.session.get(API_ORIGIN + '/api/v2/user/' + user,
                                         headers={'Accept': 'application/json'}).json()
        user_albums_uri = self.get_json_key(user_response, ['Response', 'User', 'Uris', 'UserAlbums', 'Uri'])
        if user_albums_uri is None:
            print 'Could not find URI for user\'s albums'
            return None
        # Request all albums.
        user_albums = {}
        try:
            params = {'count': '1000000'}
            if include_images:
                params['expand'] = 'AlbumImages'
            user_albums = self.session.get(API_ORIGIN + user_albums_uri, params=params,
                                           headers={'Accept': 'application/json'}).json()
        except Exception as e:
            print 'Exception getting albums :: ' + e.message
        albums_array = self.get_json_key(user_albums, ['Response', 'Album'])
        return albums_array

    def get_json_key(self, json, key_array):
        current = json
        for key in key_array:
            if not key in current:
                return None
            current = current[key]
        return current
