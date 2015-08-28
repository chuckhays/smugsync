import json

TYPE_IMAGE = "image"
TYPE_VIDEO = "video"
TYPE_OTHER = "other"

TYPE_DICTIONARY = {
  'png' : TYPE_IMAGE,
  'jpg' : TYPE_IMAGE,
  'jpeg' : TYPE_IMAGE,
  'bmp' : TYPE_IMAGE,
  'avi' : TYPE_VIDEO,
  'mpg' : TYPE_VIDEO,
  'mp4' : TYPE_VIDEO,
  'mov' : TYPE_VIDEO,
  'mts' : TYPE_VIDEO,
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
  width = None
  height = None
  exif_date = None


  def __str__(self):
    return (self.name + ' : ' + self.originalPath + ' size:(%d)') % self.size

  @classmethod
  def type_from_extension(cls, extension):
    if not extension:
      return TYPE_OTHER
    extension = extension.lower().lstrip('.')
    if extension in TYPE_DICTIONARY:
      return TYPE_DICTIONARY[extension]
    # What extension is this?
    return TYPE_OTHER


class FileEncoder(json.JSONEncoder):
  def default(self, o):
    if isinstance(o, File):
      d = o.__dict__
      return d
    else:
      return json.JSONEncoder.default(self, o)



