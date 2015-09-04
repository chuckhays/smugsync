import json
from dateutil import parser
from datetime import datetime
import hashlib

TYPE_IMAGE = "image"
TYPE_VIDEO = "video"
TYPE_OTHER = "other"
TYPE_UNKNOWN = "unknown"

TYPE_SMUGMUG = "smugmug"
TYPE_FILESYSTEM = "filesystem"

TYPE_DICTIONARY = {
  'png' : TYPE_IMAGE,
  'jpg' : TYPE_IMAGE,
  'jpeg': TYPE_IMAGE,
  'bmp' : TYPE_IMAGE,
  'gif' : TYPE_IMAGE,
  'tif' : TYPE_IMAGE,
  'cr2' : TYPE_IMAGE,
  'avi' : TYPE_VIDEO,
  'mpg' : TYPE_VIDEO,
  'mp4' : TYPE_VIDEO,
  'mov' : TYPE_VIDEO,
  'mts' : TYPE_VIDEO,
  '3gp' : TYPE_VIDEO,
  'm2t' : TYPE_VIDEO,
  'db'  : TYPE_OTHER,
  'ini' : TYPE_OTHER,
  'sh'  : TYPE_OTHER,
  'xmp' : TYPE_OTHER,
}

class File(object):
  name = None
  cTime = None
  mTime = None
  type = None
  relPath = None
  size = None
  originalPath = None
  metadata = None
  file_type = None
  md5 = None

  exif_width = None
  exif_height = None
  exif_date = None
  exif_date_parsed = None
  exif_iso = None
  exif_focal_length = None
  exif_exposure = None
  exif_camera = None
  exif_aperture = None

  def __str__(self):
    return (self.name + ' : ' + self.originalPath + ' size:(%d)') % self.size

  def get_filesystem_md5(self):
    if self.md5 is not None:
      return self.md5
    with open(self.originalPath, 'r+b') as file_to_check:
      data = file_to_check.read()
      self.md5 = hashlib.md5(data).hexdigest()
      return self.md5

  def convert_time_string(self, time_string):
    if time_string is None:
      return None
    # Example format: u'2013:02:14 12:31:58'
    try:
      if time_string == u'2013:02:14 12:31:58':
        pass
      t = datetime.strptime(time_string, '%Y:%m:%d %H:%M:%S')
      if t is not None:
        return t
    except Exception as e:
      pass
    try:
      t = parser.parse(time_string)
      if t is not None:
        return t
    except Exception as e:
      pass
    return None

  @classmethod
  def type_from_extension(cls, extension):
    if not extension:
      return TYPE_OTHER
    extension = extension.lower().lstrip('.')
    if extension in TYPE_DICTIONARY:
      return TYPE_DICTIONARY[extension]
    # What extension is this?
    return TYPE_UNKNOWN


class FileEncoder(json.JSONEncoder):
  def default(self, o):
    if isinstance(o, File):
      d = o.__dict__
      return d
    else:
      return json.JSONEncoder.default(self, o)



