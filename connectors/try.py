import filesystem

def main():
  fs = filesystem.FileSystemConnector('c:\\users\\chuck\\documents\\github')
  files = fs.enumerate_objects()
  for f in files:
    print f

if __name__ == "__main__":
    main()