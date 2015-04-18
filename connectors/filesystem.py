import datetime
import os
from connectorbase import ConnectorBase
from file import File

class FileSystemConnector(ConnectorBase):
        
  def enumerate_objects(self):
    files = []
    # Recursively list all of the files under root.
    allFiles = [self.create_file(dir, f) for dir, dirs, files in os.walk(self.root) for f in files]
    return allFiles

  def create_file(self, filePath, fileName):
    file = File()
    file.name = fileName
    file.relPath = os.path.relpath(filePath, self.root)
    file.originalPath = os.path.join(filePath, fileName)
    t = os.path.getmtime(file.originalPath)
    file.mTime = datetime.datetime.fromtimestamp(t)
    t = os.path.getctime(file.originalPath)
    file.cTime = datetime.datetime.fromtimestamp(t)
    file.size = os.path.getsize(file.originalPath)

    _, fileExtension = os.path.splitext(file.originalPath)
    file.type = File.type_from_extension(fileExtension)

    return file


