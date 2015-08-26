import filesystem
import smugmug
import connectorbase
import json


def main():
  fs = filesystem.FileSystemConnector( { connectorbase.ROOT_KEY: 'e:\\' } )
  fs_files = fs.enumerate_objects()
  #for f in files:
  #  print f

  config_data = {}
  config_data[smugmug.APP_NAME_KEY] = 'XXXX'
  config_data[smugmug.API_KEY_KEY] = 'XXXX'
  config_data[smugmug.OAUTH_SECRET_KEY] = 'XXXX'
  config_data[connectorbase.ROOT_KEY] = '/'
  sm = smugmug.SmugMugConnector(config_data)


  sm.authenticate()
  def match(file, file_array):
    if file is None or file_array is None:
      return None
    for f in file_array:
      if (f.name == file.name and
          f.size == file.size):
        return f
    return None


  sm_files = sm.enumerate_objects()
  #for f in files:
 #   print json.dumps(f, indent = 2)

  both =[]
  sm = []
  fs = []

  for fs_file_key in fs_files:
    fs_file_array = fs_files[fs_file_key]
    sm_file_array = []
    if fs_file_key in sm_files:
      sm_file_array = sm_files[fs_file_key]

    for fs_file in fs_file_array:
      # Try to find a match in sm_files_array
      matched_file = match(fs_file, sm_file_array)
      if (matched_file is not None):
        # Matched, put file in both and remove from both.
        both.append(fs_file)
        fs_file_array.remove(fs_file)
        sm_file_array.remove(matched_file)
      else:
        # Put in fs only and remove from fs_files.
        fs.append(fs_file)
        fs_file_array.remove(fs_file)
  for sm_file_key in sm_files:
    sm_file_array = sm_files[sm_file_key]
    # Add to sm.
    sm.extend(sm_file_array)

  print 'Both: %d SM: %d FS: %d' % (len(both), len(sm), len(fs))


if __name__ == "__main__":
    main()