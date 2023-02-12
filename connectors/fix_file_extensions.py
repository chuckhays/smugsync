import os
import subprocess

ROOT = 'e:\\'

def main():
  total_renames = 0
  for dir, dirs, files in os.walk(ROOT):
      for f in files:
        path = os.path.normpath(os.path.join(dir, f))
        without_extension, fileExtension = os.path.splitext(path)
        fileExtension = fileExtension.lower().lstrip('.')
        if fileExtension == 'db':
          continue
        result = subprocess.check_output(['file', '-b', '--mime-type', path], stderr=subprocess.STDOUT)

        actual_extension = None
        if result is None:
          print('No type for: ' + path)
        elif 'image/jpeg' in result:
          actual_extension = 'JPG'
        elif 'image/gif' in result:
          actual_extension = 'GIF'
        elif 'image/png' in result:
          actual_extension = 'PNG'
        elif 'video/quicktime' in result:
          actual_extension = 'MOV'
        elif 'video/mp4' in result:
          actual_extension = 'MP4'
        else:
          print('Unknown type: ' + result + ' : ' + path)

        if actual_extension is None:
          continue

        if fileExtension != actual_extension.lower():
          if fileExtension == 'jpeg' and actual_extension.lower() == 'jpg':
            print('skipped jpeg->jpg')
            continue
          try:
            total_renames += 1
            new_path = without_extension + '.' + actual_extension
            print('Need to fix extension of ' + path + ' to: ' + new_path)
            #uncomment to do actual renames
            #os.rename(path, new_path)
          except Exception as e:
            print('Exception renaming file: ' + e)
  print('done, total renames : %d' % total_renames)


if __name__ == "__main__":
  try:
    main()
  except Exception as e:
    print('Exception: ' + e.message)
