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

  def authenticate(self):
    filename = self.data_file
    if not filename:
      filename = "smugmug.data"
    data = {}
    if os.path.exists(filename):
      with open(filename, 'r') as json_data:
        data = json.load(json_data)
    # Check for cached accessToken
    accessToken = data.get(ACCESS_TOKEN_KEY)
    if not accessToken:
      smugmug = SmugMug(api_key=self.api_key, oauth_secret=self.oauth_secret, app_name=self.app_name)

      response = smugmug.auth_getAccessToken()
      # If we want to write to smugmug, need to change perm.
      url = smugmug.authorize(access="Full", perm="Read")
      requestToken = response['Auth']
      input('Visit %s to authorize app and press enter when complete.\n' % (url))

      smugmug = SmugMug(api_key=self.api_key, oauth_secret=self.oauth_secret, oauth_token=requestToken['Token']['id'],
                        oauth_token_secret=requestToken['Token']['Secret'], app_name=self.app_name)
      response = smugmug.auth_getAccessToken()
      accessToken = response['Auth']

      with open(filename, 'w') as json_data:
        json.dump(accessToken, json_data)

    self.smugmug = SmugMug(api_key=self.api_key, oauth_secret=self.oauth_secret, oauth_token=accessToken['Token']['id'],
                           oauth_token_secret=accessToken['Token']['Secret'], app_name=self.app_name)
    return True








        
  def enumerate_objects(self):
    pass