class ConnectorBase:

    def __init__(self, root):
        self.root = root

    def enumerate_objects(self):
        raise NotImplementedError("Please Implement this method")
        
