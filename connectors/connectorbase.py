ROOT_KEY = "rootPath"
DATA_FILE_KEY = "dataFile"

class ConnectorBase(object):

    def __init__(self, config_data):
      self.config_data = config_data
      self.root = config_data.get(ROOT_KEY)
      self.data_file = config_data.get(DATA_FILE_KEY)

    def enumerate_objects(self):
      raise NotImplementedError("Please implement this method.")

    def authenticate(self):
      raise NotImplementedError("Please implement this method.")
        
