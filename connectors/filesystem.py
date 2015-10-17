import datetime
import os
from connectorbase import ConnectorBase
from file import File
import file as fileConstants
from PIL import Image, ExifTags
import shelve
import json

from clint.textui import progress
from dateutil import parser

CACHE_FILE_NAME = 'filesystem.cache'
SAVE_EVERY = 5000


class FileSystemConnector(ConnectorBase):

  def __init__(self, config_data):
    super(FileSystemConnector, self).__init__(config_data)
    self.shelve = None
    self.count = 0
    self.bar = progress.Bar(label="progress to save", expected_size=SAVE_EVERY)
    self.changed = False

  def authenticate(self, config_file):
    return True
        
  def enumerate_objects(self):
    print 'Enumerating files in %s' % self.root
    ignore_dir = os.path.join(self.root, 'ignore')
    results = {}
    # Recursively list all of the files under root.
    #file_pairs = []
    for dir, dirs, files in os.walk(self.root):
      if ignore_dir in dir:
        continue
      for f in files:
        file_object = self.create_file(dir, f)
        if file_object is not None:
          #print 'Got valid file: ' + f
          self.add_file_to_hash(file_object, results)
    if self.changed:
      self.save_cache()
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
    if file.type == fileConstants.TYPE_OTHER or file.type == fileConstants.TYPE_UNKNOWN:
      return None
    self.update_exif_metadata(file)
    file.file_type = fileConstants.TYPE_FILESYSTEM
    return file

  def update_exif_metadata(self, file):
    # Check cached exif data, if not fetch exif.
    exif = None
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
        exif['md5'] = file.get_filesystem_md5()
      except:
        exif = {}
      self.put_cache(file, exif)

    # If we don't have md5 (maybe missing exif data), store it.
    if 'md5' not in exif:
      exif['md5'] = file.get_filesystem_md5()
      self.put_cache(file, exif)

    file.metadata = exif
    file.md5 = self.get_json_key(exif, ['md5'])
    file.exif_width = self.get_json_key(exif, ['ImageWidth']) or self.get_json_key(exif, ['ExifImageWidth'])
    file.exif_height = self.get_json_key(exif, ['ImageLength']) or self.get_json_key(exif, ['ExifImageHeight'])
    ap = self.get_json_key(exif, ['ApertureValue'])
    # ap is a tuple, store as a truncated double to 1 decimal place
    try:
      raw_ap = ap[0]/float(ap[1])
      truncated_ap = self.trunc(raw_ap, 1)
      file.exif_aperture = truncated_ap
    except:
      pass
    file.exif_aperture = self.get_json_key(exif, ['Aperture'])
    file.exif_date = self.get_json_key(exif, ['DateTimeOriginal'])
    file.exif_date_parsed = file.convert_time_string(file.exif_date)
    file.exif_iso = self.get_json_key(exif, ['ISOSpeedRatings'])
    fl = self.get_json_key(exif, ['FocalLength'])
    # fl is a tuple, store as double truncated to 1 decimal place
    try:
      file.exif_focal_length = self.trunc(fl[0]/float(fl[1]), 1)
    except:
      pass
    et = self.get_json_key(exif, ['ExposureTime'])
    # et is a tuple, store as a fraction string
    try:
      file.exif_exposure = '%d/%d' % (et[0], et[1])
    except:
      pass
    file.exif_camera = self.get_json_key(exif, ['Model'])

  def trunc(self, num, digits):
   sp = str(num).split('.')
   return '.'.join([sp[0], sp[1][:digits]])

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
    self.changed = True
    file_key = str(file.originalPath)
    data = {
      'lastupdated' : file.mTime,
      'exif' : exif,
    }
    self.shelve[file_key] = data
    self.count += 1
    self.bar.show(self.count)
    if self.count % 5000 == 0:
      self.count = 0
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