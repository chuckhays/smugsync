import filesystem
import smugmug
import connectorbase
import json
from PIL import Image, ExifTags
import time
from clint.textui import progress

from file import FileEncoder
import pprint

def main():
  start = time.clock()
  fs = filesystem.FileSystemConnector( { connectorbase.ROOT_KEY: 'e:\\' } )
  fs_files = fs.enumerate_objects()
  end_fs = time.clock()
  print 'Finished FS, time elapsed: %f' % (end_fs - start)
  #for fs_key in fs_files:
  #    print f.originalPath

  start = time.clock()
  config_data = {}
  try:
    with open('smugmug.keys', 'r') as keys_file:
      config_data = json.load(keys_file)
  except Exception as e:
    pass
  sm = smugmug.SmugMugConnector(config_data)
  sm.authenticate()
  sm_files = sm.enumerate_objects()
  end_sm = time.clock()
  print 'Finished SM, time elapsed: %f' % (end_sm - start)
  print '\r\n'
  print '\r\n'



  def match(file, file_array):
    if file is None or file_array is None:
      return (None, False)
    for f in file_array:
      if f.name == file.name:
        # if sizes match, this is a match
        if f.size == file.size and f.size is not None:
          return (f, False)
        # if sizes are close, check exif data
        size_diff = abs(file.size - f.size) / f.size
        if size_diff > 0.05:
          continue
        # check height/width, camera model
        if f.exif_height == file.exif_height and f.exif_height is not None and f.exif_width == file.exif_width and f.exif_height is not None:
          if f.exif_camera == file.exif_camera and f.exif_camera is not None:
            return (f, True)
    if file.name == 'IMG_3329.JPG':
      print '#################################################'
      print '#################################################'
      pp = pprint.PrettyPrinter(indent=2)
      pp.pprint(file.__dict__)
      for f in file_array:
        print '@@@@@@@@@@@@@@@@@@@@@@@@@'
        pp.pprint(f.__dict__)
    return (None, False)


  #for f in files:
 #   print json.dumps(f, indent = 2)

  print 'Starting file matching'
  start = time.clock()
  both =[]
  sm = []
  fs = []
  fuzzy = 0


  print 'matching files'
  for fs_file_key in progress.bar(fs_files):
    fs_file_array = fs_files[fs_file_key]
    sm_file_array = []
    if fs_file_key in sm_files:
      sm_file_array = sm_files[fs_file_key]

    for fs_file in fs_file_array:
      # Try to find a match in sm_files_array
      matched_file, fuzzy = match(fs_file, sm_file_array)
      if fuzzy:
        fuzzy += 1
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

  print 'Both: %d SM: %d FS: %d fuzzy: %d' % (len(both), len(sm), len(fs), fuzzy)


if __name__ == "__main__":
    main()