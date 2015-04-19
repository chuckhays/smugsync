import connectors.file as fileType
from connectors.file import File
from connectors.filesystem import FileSystemConnector
import mock
import unittest

class FileTest(unittest.TestCase):

  def setUp(self):
    print('In setUp()')

  def tearDown(self):
    print('In tearDown()')

  @mock.patch('os.path.getsize')
  @mock.patch('os.path.getmtime')
  @mock.patch('os.path.getctime')
  @mock.patch('os.walk')

  def test_enumerate(self, mock_os_walk, mock_mtime, mock_ctime, mock_size):
    mock_os_walk.return_value = [
        ('/foo', ('bar',), ('baz',)),
        ('/foo/bar', (), ('spam', 'eggs')),
    ]
    mock_mtime.return_value = 'abc'
    mock_ctime.return_value = 'def'
    mock_size.return_value = 300
    fc = FileSystemConnector('/tmp')
    list = fc.enumerate_objects()
    print "asdasdas"
    for f in list:
      print f.name
      print f.originalPath
      print f.relPath
      print f.size


  def test_type_from_extension(self):
    assert fileType.TYPE_IMAGE == File.type_from_extension('PnG')
    assert fileType.TYPE_IMAGE == File.type_from_extension('PnG')
    assert fileType.TYPE_IMAGE == File.type_from_extension('BMP')
    assert fileType.TYPE_IMAGE == File.type_from_extension('jpg')
    assert fileType.TYPE_VIDEO == File.type_from_extension('avi')
    assert fileType.TYPE_OTHER == File.type_from_extension('vi')
    assert fileType.TYPE_OTHER == File.type_from_extension('')
    assert fileType.TYPE_OTHER == File.type_from_extension(None)

if __name__ == '__main__':
  unittest.main()



