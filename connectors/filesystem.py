import datetime
import os
from connectorbase import ConnectorBase
from file import File
from PIL import Image, ExifTags
import shelve

from clint.textui import progress
from dateutil import parser

CACHE_FILE_NAME = 'filesystem.cache'

class FileSystemConnector(ConnectorBase):

  def __init__(self, config_data):
    super(FileSystemConnector, self).__init__(config_data)
    self.shelve = None

  def authenticate(self, config_file):
    return True
        
  def enumerate_objects(self):
    print 'Enumerating files in %s' % self.root
    results = {}
    # Recursively list all of the files under root.
    #file_pairs = []
    for dir, dirs, files in os.walk(self.root):
      for f in files:
        fileObject = self.create_file(dir, f)
        self.add_file_to_hash(fileObject, results)
    return results

  def create_file(self, filePath, fileName):
    file = File()
    file.name = fileName
    file.relPath = os.path.normpath(os.path.relpath(filePath, self.root))
    file.originalPath = os.path.normpath(os.path.join(filePath, fileName))
    t = os.path.getmtime(file.originalPath)
    file.mTime = datetime.datetime.fromtimestamp(t)
    t = os.path.getctime(file.originalPath)
    file.cTime = datetime.datetime.fromtimestamp(t)
    file.size = os.path.getsize(file.originalPath)
    _, fileExtension = os.path.splitext(file.originalPath)
    file.type = File.type_from_extension(fileExtension)
    self.update_exif_metadata(file)
    return file

  def update_exif_metadata(self, file):
    # Check cached exif data, if not fetch exif.
    try:
      exif = self.check_cache(file)
    except Exception as e:
      print 'Exception checking cached data for file: ' + file.originalPath + ' :: ' + e.message
    if exif is None:
      img = None
      try:
        img = Image.open(file.originalPath)
        exif = {
          ExifTags.TAGS[k]: v
          for k, v in img._getexif().items()
          if k in ExifTags.TAGS
        }
      except:
        exif = {}
      self.put_cache(file, exif)
    file.metadata = exif

  def check_cache(self, file):
    file_key = str(file.originalPath)
    self.init_cache()
    if not file_key in self.shelve:
      return None
    data = self.shelve[file_key]
    cached_mtime = self.get_json_key(data, ['lastupdated'])
    if cached_mtime is None:
      return None
    if file.mTime is None:
      return None
    if cached_mtime < file.mTime:
      return None
    return self.get_json_key(data, ['exif'])

  def put_cache(self, file, exif):
    file_key = str(file.originalPath)
    data = {
      'lastupdated' : file.mTime,
      'exif' : exif,
    }
    self.shelve[file_key] = data
    self.save_cache()

  def init_cache(self):
    if self.shelve is None:
      self.shelve = shelve.open(CACHE_FILE_NAME, writeback = True)

  def save_cache(self):
    self.shelve.sync()

  def get_json_key(self, json, key_array):
    current = json
    for key in key_array:
      if not key in current:
        return None
      current = current[key]
    return current