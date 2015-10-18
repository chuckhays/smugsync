import connectors.file as fileType
from connectors.file import File
from connectors.filesystem import FileSystemConnector
import connectors.connectorbase as connectorbase
import mock
import unittest


class FileTest(unittest.TestCase):
    def setUp(self):
        print('In setUp()')

    def tearDown(self):
        print('In tearDown()')

    def test_type_from_extension(self):
        assert fileType.TYPE_IMAGE == File.type_from_extension('PnG')
        assert fileType.TYPE_IMAGE == File.type_from_extension('PnG')
        assert fileType.TYPE_IMAGE == File.type_from_extension('BMP')
        assert fileType.TYPE_IMAGE == File.type_from_extension('jpg')
        assert fileType.TYPE_VIDEO == File.type_from_extension('avi')
        assert fileType.TYPE_UNKNOWN == File.type_from_extension('vi')
        assert fileType.TYPE_OTHER == File.type_from_extension('')
        assert fileType.TYPE_OTHER == File.type_from_extension(None)


if __name__ == '__main__':
    unittest.main()
