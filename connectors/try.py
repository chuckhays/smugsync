import filesystem
import smugmug
import connectorbase

def main():
  fs = filesystem.FileSystemConnector( { connectorbase.ROOT_KEY: 'c:\\users\\chuck\\documents\\github' } )
 # files = fs.enumerate_objects()
 # for f in files:
 #   print f

  config_data = {}
  config_data[smugmug.APP_NAME_KEY] = 'smug8'
  config_data[smugmug.API_KEY_KEY] = 'XXXXX'
  config_data[smugmug.OAUTH_SECRET_KEY] = 'XXXXX'
  config_data[connectorbase.ROOT_KEY] = '/'
  sm = smugmug.SmugMugConnector(config_data)


  sm.authenticate()

  files = sm.enumerate_objects()
  for f in files:
    print f

if __name__ == "__main__":
    main()