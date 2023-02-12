from . import filesystem
from . import smugmug
from . import connectorbase
import json
from PIL import Image, ExifTags
import time
from clint.textui import progress
from .file import File
from . import file as fileConstants
import os
import shutil
import traceback
import configparser

from .file import FileEncoder
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
      md51 = None
      if file1.file_type == fileConstants.TYPE_FILESYSTEM:
        md51 = file1.get_filesystem_md5()
      else:
        md51 = file1.md5
      md52 = None
      if file2.file_type == fileConstants.TYPE_FILESYSTEM:
        md52 = file2.get_filesystem_md5()
      else:
        md52 = file2.md5
      if md51 is not None and md51 == md52:
        return True
    # if sizes are close, check exif data
    size_diff = abs(file1.size - file2.size) / float(file2.size)
    if size_diff > 0.05:
      return False
    # check height/width, camera model
    if file1.exif_height is None or file1.exif_width is None:
      return False
    sizes_match = file1.exif_height == file2.exif_height and file1.exif_width == file2.exif_width
    if not sizes_match:
      sizes_match = file1.exif_height == file2.exif_width and file1.exif_width == file2.exif_height
    if sizes_match:
      #if file1.exif_camera == file2.exif_camera and file1.exif_camera is not None:
      if file1.exif_date_parsed is not None and file1.exif_date_parsed == file2.exif_date_parsed:
        pass #return True
  return False

def mirror(smc, smugmug, fs_folder, fs_file):
  # Make sure the destination path exists
  path = smugmug.relativePath
  if path is None:
    print('Error: no relative path for file: ' + file.originalPath)
    return
  path = path.lstrip('\\')
  path = os.path.normpath(os.path.join(fs_folder, path))
  dst = os.path.join(path, smugmug.name)

  # Check if file is already there, skip it if it is.
  if os.path.isfile(dst):
    return

  try:
    os.makedirs(path)
  except OSError:
    if not os.path.isdir(path):
        raise


  # If we have a fs file, copy from there, if not, fetch from smugmug.
  if fs_file:
    src = fs_file.originalPath
    shutil.copy2(src, dst)
  else:
    smc.download(smugmug, dst)

def main():
  start = time.clock()

  config = configparser.SafeConfigParser({'dest_path': 'e:\\'})
  config.read("smugsync.cfg")
  dest_path = config.get('smugsync', 'dest_path')

  fs = filesystem.FileSystemConnector( { connectorbase.ROOT_KEY: dest_path } )
  fs_files = fs.enumerate_objects()
  end_fs = time.clock()
  print('Finished FS, time elapsed: %f' % (end_fs - start))

  start = time.clock()
  config_data = {}
  try:
    with open('smugmug.keys', 'r') as keys_file:
      config_data = json.load(keys_file)
  except Exception as e:
    pass
  smc = smugmug.SmugMugConnector(config_data)
  smc.authenticate()
  sm_files = smc.enumerate_objects()
  end_sm = time.clock()
  print('Finished SM, time elapsed: %f' % (end_sm - start))
  print('\r\n')
  print('\r\n')

  #for f in files:
 #   print json.dumps(f, indent = 2)

  sm_count = 0
  fs_count = 0
  for sm_k in sm_files:
    sm_count += len(sm_files[sm_k])
  for fs_k in fs_files:
    fs_count += len(fs_files[fs_k])

  print('SM total: %d  FS total: %d' % (sm_count, fs_count))
  print('Starting file matching')
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
      print('Exception on ' + fs_file_key + ' :: ' + e.message)

  for sm_file_key in sm_files:
    combined_files[sm_file_key] = sm_files[sm_file_key]

  #csv = open('files.csv', 'w')
  for file_key in progress.bar(combined_files):
    files_array = combined_files[file_key]
    matched_sets = match_sets(files_array)
    all_both = True
    for set in matched_sets:
      has_sm = False
      has_fs = False
      sm_file = None
      fs_file = None
      for f in set:
        if f.file_type == fileConstants.TYPE_SMUGMUG:
          sm_file = sm_file if not sm_file is None else f
          has_sm = True
        if f.file_type == fileConstants.TYPE_FILESYSTEM:
          fs_file = fs_file if not fs_file is None else f
          has_fs = True
      if has_sm and has_fs:
        both.append(set)
        mirror(smc, sm_file, dest_path, fs_file)
      elif has_sm:
        sm.append(set)
        mirror(smc, sm_file, dest_path, None)
        all_both = False
      else:
        fs.append(set)
        all_both = False
    #if not all_both:
    #  for set in matched_sets:
    #    csv.write(file_key)
    #    csv.write(',')
    #    for csv_file in set:
    #      csv.write('%s,%d,' % (csv_file.originalPath, csv_file.size))
    #    csv.write('\r\n')
  #csv.close()
  print('Done: %f sec' % (time.clock()-start))
  print('Both: %d SM: %d FS: %d fuzzy: %d' % (len(both), len(sm), len(fs), fuzzy))

  # Mirror smugmug to local path
  # If we can find a matched pair, we have an md5sum identical file we can use.


if __name__ == "__main__":
  try:
    main()
  except Exception as e:
    print('Exception: ' + e.message)
    tb = traceback.format_exc()
    print(tb)
