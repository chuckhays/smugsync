import json
import os
import shutil
import sys
import threading
from urllib.parse import urlsplit, urlunsplit, parse_qsl
from urllib.parse import urlencode

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

# Maximum number of threads to use when getting all album images.
# Effectively sets the number of HTTP requests at once.
MAX_THREADS = 10


class Smugmug(object):
    def __init__(self, api_key=None, oauth_secret=None, app_name=None, access_cache_file='smugmug.access'):
        self.api_key = api_key
        self.oauth_secret = oauth_secret
        self.app_name = app_name
        self.access_token = None
        self.access_token_secret = None
        self.access_cache_file = access_cache_file
        self.session = None
        self.max_threads_lock = threading.Semaphore(MAX_THREADS)
        self.album_images_lock = threading.Lock()

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
            print(('Go to %s in a web browser.' % auth_url))
            sys.stdout.write('Enter the six-digit code: ')
            sys.stdout.flush()
            verifier = sys.stdin.readline().strip()
            at, ats = service.get_access_token(rt, rts, params={'oauth_verifier': verifier})
            print(('Access token: %s' % at))
            print(('Access token secret: %s' % ats))
            self.access_token = at
            self.access_token_secret = ats
            # Cache access token and access token secret so we don't have to authenticate on the next run.
            with open(self.access_cache_file, 'w') as json_data:
                json.dump({ACCESS_TOKEN_KEY: self.access_token, ACCESS_TOKEN_SECRET_KEY: self.access_token_secret},
                          json_data)
        self.session = OAuth1Session(self.api_key, self.oauth_secret, access_token=self.access_token,
                                     access_token_secret=self.access_token_secret)

    def get_authorized_user(self):
        if self.session is None:
            self.authenticate()
        auth_user_response = self.session.get(API_ORIGIN + '/api/v2!authuser',
                                              headers={'Accept': 'application/json'}).json()
        authed_user = self.get_json_key(auth_user_response, ['Response', 'User', 'Name'])
        return authed_user

    def get_albums(self, user, include_images=False):
        if self.session is None:
            self.authenticate()
        user_response = self.session.get(API_ORIGIN + '/api/v2/user/' + user,
                                         headers={'Accept': 'application/json'}).json()
        user_albums_uri = self.get_json_key(user_response, ['Response', 'User', 'Uris', 'UserAlbums', 'Uri'])
        if user_albums_uri is None:
            print('Could not find URI for user\'s albums')
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
            print('Exception getting albums :: ' + e.message)
        albums_array = self.get_json_key(user_albums, ['Response', 'Album'])
        return albums_array

    def get_album_images(self, album):
        album_last_updated_string = self.get_json_key(album, ['ImagesLastUpdated'])
        album_uri = self.get_json_key(album, ['Uris', 'AlbumImages', 'Uri'])
        if album_uri is None:
            print('Could not find album images uri for album: ' + self.get_json_key(album, ['Name']))
            return
        cached_album_images_response = self.session.get(API_ORIGIN + album_uri,
                                                        params={'count': '1000000', '_expand': 'ImageMetadata',
                                                                '_expandmethod': 'inline'},
                                                        headers={'Accept': 'application/json'})
        try:
            cached_album_images = cached_album_images_response.json()
        except Exception as e:
            print('Exception getting album :: ' + album_uri + ' :: ' + e.message + ' :: (%d)' % cached_album_images_response.status_code)
            return
        images_array = self.get_json_key(cached_album_images, ['Response', 'AlbumImage'])
        if images_array is None:
            print('Could not get images array for album: ' + self.get_json_key(album, ['Name']) + 'uri:' + album_uri)
            images_array = []
        return images_array

    def _get_album_images_worker(self, album, output):
        with self.max_threads_lock:
            print('Starting: ' + self.get_json_key(album, ['Name']))
            album_images = self.get_album_images(album)
            with self.album_images_lock:
                output[self.get_json_key(album, ['Uri'])] = album_images

    def get_all_album_images(self, albums):
        threads = []
        output = {}
        for album in albums:
            thread = threading.Thread(target=self._get_album_images_worker, args=(album, output,))
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
        return output

    def download(self, album_image, destination_folder, overwrite_if_exists=False):
        source_uri = self.get_json_key(album_image, ['ArchivedUri'])
        if source_uri is None:
            print('Error downloading image, could not get uri.')
            return False
        filename = self.get_json_key(album_image, ['FileName'])
        filename = self.sanitize_filename(filename)
        if filename is None:
            print('Error downloading image, could not get file name.')
            return False
        destination_file = os.path.join(destination_folder, filename)
        if os.path.isfile(destination_file) and not overwrite_if_exists:
            # File already exists.
            return True
        try:
            print('Downloading: (' + filename + ') ' + source_uri)
            r = self.session.get(source_uri, stream=True)
            if r.status_code == 200:
                with open(destination_file, 'wb') as f:
                    r.raw.decode_content = True
                    shutil.copyfileobj(r.raw, f)
            else:
                print(('Response code %d for : ' % r.status_code) + source_uri)
                return False
        except Exception as e:
            print('Exception downloading file at: ' + source_uri + ' :: ' + e)
            return False
        return True

    # TODO: add option to delete images that exist in the mirror but not on SmugMug.
    def mirror_album_images(self, album_images, destination_folder_path):
        if destination_folder_path is None:
            print('Must supply a destination path')
            return False
        # Create the folder if it doesn't exist.
        try:
            os.makedirs(destination_folder_path)
        except OSError:
            if not os.path.isdir(destination_folder_path):
                raise
        success = True
        for album_image in album_images:
            if not self.download(album_image, destination_folder_path):
                success = False
        return success

    def mirror_album(self, album, destination_root_path):
        if destination_root_path is None:
            print('Must supply a destination root path.')
            return False
        relative_path = os.path.normpath(self.get_json_key(album, ['UrlPath']))
        if relative_path is None:
            print('Could not get relative path from album.')
            return False
        destination_path = relative_path.lstrip('\\')
        destination_path = os.path.normpath(os.path.join(destination_root_path, destination_path))
        album_images = self.get_album_images(album)
        return self.mirror_album_images(album_images, destination_path)

    def _mirror_albums_worker(self, album, destination_root_path):
        with self.max_threads_lock:
            print('Starting mirroring of: ' + self.get_json_key(album, ['Name']))
            self.mirror_album(album, destination_root_path)

    def mirror_albums(self, albums, destination_root_path):
        threads = []
        for album in albums:
            thread = threading.Thread(target=self._mirror_albums_worker, args=(album, destination_root_path,))
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

    def get_json_key(self, input_json, key_array):
        current = input_json
        for key in key_array:
            if key not in current:
                return None
            current = current[key]
        return current

    def sanitize_filename(self, filename):
        # Allows file names to contain alphanumerics and anything within keep_characters
        return "".join(c for c in filename if c.isalnum() or c in keep_characters).rstrip()
