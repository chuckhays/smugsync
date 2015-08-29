import filesystem
import smugmug
import connectorbase
import json
from PIL import Image, ExifTags
import time


def main():
  start = time.clock()
  fs = filesystem.FileSystemConnector( { connectorbase.ROOT_KEY: 'd:\\pics' } )
  fs_files = fs.enumerate_objects()
  end_fs = time.clock()
  print 'Finished FS, time elapsed: %f' % (end_fs - start)
  #for fs_key in fs_files:
  #    print f.originalPath

  config_data = {}
  try:
    with open('smugmug.keys', 'r') as keys_file:
      config_data = json.load(keys_file)
  except Exception as e:
    pass
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