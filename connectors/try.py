import filesystem
import smugmug
import connectorbase
import json
from PIL import Image, ExifTags
import time
from clint.textui import progress
from file import File
import file as fileConstants

from file import FileEncoder
import pprint

def match_sets(file_array):
  if file_array is None:
    return []

  result_sets = []
  files = list(file_array)
  while len(files) > 0:
    first_file = files[0]
    rest_files = files[1:]
    matching_files = match(first_file, rest_files)
    matching_files.append(first_file)
    result_sets.append(matching_files)
    for f in matching_files:
      files.remove(f)
  return result_sets

def match(file, files):
  if files is None:
    return []
  matching_files = [f for f in files if do_files_match(file, f)]
  return matching_files

def do_files_match(file1, file2):
  if file1 is None or file2 is None:
    return False
  if file1.name == file2.name:
    # if sizes match, this is a match
    if file1.size == file2.size and file1.size is not None:
      return True
    # if sizes are close, check exif data
    size_diff = abs(file1.size - file2.size) / float(file2.size)
    if size_diff > 0.05:
      return False
    # check height/width, camera model
    if file1.exif_height == file2.exif_height and file1.exif_height is not None and file1.exif_width == file2.exif_width and file1.exif_height is not None:
      #if file1.exif_camera == file2.exif_camera and file1.exif_camera is not None:
        return True
  return False

def main():
  start = time.clock()
  fs = filesystem.FileSystemConnector( { connectorbase.ROOT_KEY: 'e:\\' } )
  fs_files = fs.enumerate_objects()
  end_fs = time.clock()
  print 'Finished FS, time elapsed: %f' % (end_fs - start)

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




  #for f in files:
 #   print json.dumps(f, indent = 2)

  print 'Starting file matching'
  start = time.clock()
  both =[]
  sm = []
  fs = []
  fuzzy = 0

  combined_files = {}

  for fs_file_key in fs_files:
    try:
      # combine all the files into a single list
      files_array = []
      fs_file_array = fs_files[fs_file_key]
      if fs_file_array is not None:
        files_array += fs_file_array
      sm_file_array = []
      if fs_file_key in sm_files:
        sm_file_array = sm_files[fs_file_key]
        sm_files.pop(fs_file_key)
      if sm_file_array is not None:
        files_array += sm_file_array
      combined_files[fs_file_key] = files_array
    except Exception as e:
      print 'Exception on ' + fs_file_key + ' :: ' + e.message

  for sm_file_key in sm_files:
    combined_files[sm_file_key] = sm_files[sm_file_key]

  for file_key in combined_files:
    files_array = combined_files[file_key]
    matched_sets = match_sets(files_array)
    for set in matched_sets:
      has_sm = False
      has_fs = False
      for f in set:
        if f.file_type == fileConstants.TYPE_SMUGMUG:
          has_sm = True
        if f.file_type == fileConstants.TYPE_FILESYSTEM:
          has_fs = True
      if has_sm and has_fs:
        both.append(set)
      elif has_sm:
        sm.append(set)
      else:
        fs.append(set)

  print 'Both: %d SM: %d FS: %d fuzzy: %d' % (len(both), len(sm), len(fs), fuzzy)


if __name__ == "__main__":
  try:
    main()
  except Exception as e:
    print 'Exception: ' + e.message
