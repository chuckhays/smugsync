ROOT_KEY = "rootPath"
DATA_FILE_KEY = "dataFile"

class ConnectorBase(object):

    def __init__(self, config_data):
      self.config_data = config_data
      self.root = config_data.get(ROOT_KEY)
      self.data_file = config_data.get(DATA_FILE_KEY)

    # This should return a dictionary with lowercase file name as the key, and the value should
    # be an array of file objects with that file name.
    def enumerate_objects(self):
      raise NotImplementedError("Please implement this method.")

    def authenticate(self):
      raise NotImplementedError("Please implement this method.")

    def add_file_to_hash(self, file, hash):
      if file is None:
        return
      key = file.name.lower()
      if not key in hash:
        hash[key] = []
      hash[key].append(file)
        
