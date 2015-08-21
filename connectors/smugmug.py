import datetime
import os
from connectorbase import ConnectorBase
from file import File
from smugpy import SmugMug
import sys
import json

API_KEY_KEY = "apiKey"
OAUTH_SECRET_KEY = "oauthSecret"
APP_NAME_KEY = "appName"
ACCESS_TOKEN_KEY = "accessToken"

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
    if not self.access_token:
      smugmug = SmugMug(api_key=self.api_key, oauth_secret=self.oauth_secret, app_name=self.app_name, api_version='2.0')

      response = smugmug.auth_getRequestToken()
      # If we want to write to smugmug, need to change perm.
      url = smugmug.authorize(access="Public", perm="Read")
      requestToken = response['Auth']
      raw_input('Visit %s to authorize app and press enter when complete.\n' % (url))

      smugmug = SmugMug(api_key=self.api_key, oauth_secret=self.oauth_secret, oauth_token=requestToken['Token']['id'],
                        oauth_token_secret=requestToken['Token']['Secret'], app_name=self.app_name, api_version='2.0')
      response = smugmug.auth_getAccessToken()
      self.access_token = response['Auth']

      with open(filename, 'w') as json_data:
        json.dump({ ACCESS_TOKEN_KEY : self.access_token }, json_data)

    self.smugmug = SmugMug(api_key=self.api_key, oauth_secret=self.oauth_secret, oauth_token=self.access_token['Token']['id'],
                           oauth_token_secret=self.access_token['Token']['Secret'], app_name=self.app_name, api_version='2.0')
    return True

  def enumerate_objects(self):
    albums = self.smugmug.albums_get(NickName=self.access_token['User']['NickName'])
    for album in albums["Albums"]:
      print("%s, %s" % (album["id"], album["Title"]))
    return []