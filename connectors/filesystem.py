import datetime
import os
from connectorbase import ConnectorBase
from file import File
from PIL import Image, ExifTags

class FileSystemConnector(ConnectorBase):

  def authenticate(self, config_file):
    return True
        
  def enumerate_objects(self):
    print 'Enumerating files in %s' % self.root
    results = {}
    # Recursively list all of the files under root.
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

    #img = Image.open(file.originalPath)
    #exif = {
    #  ExifTags.TAGS[k]: v
    #  for k, v in img._getexif().items()
    #  if k in ExifTags.TAGS
    #}
    #file.metadata = exif

    return file


