import connectors.file as fileType
from connectors.file import File

def test_type_from_extension():
  assert fileType.TYPE_IMAGE == File.type_from_extension('PnG')
  assert fileType.TYPE_IMAGE == File.type_from_extension('PnG')
  assert fileType.TYPE_IMAGE == File.type_from_extension('BMP')
  assert fileType.TYPE_IMAGE == File.type_from_extension('jpg')
  assert fileType.TYPE_VIDEO == File.type_from_extension('avi')
  assert fileType.TYPE_OTHER == File.type_from_extension('vi')
  assert fileType.TYPE_OTHER == File.type_from_extension('')
  assert fileType.TYPE_OTHER == File.type_from_extension(None)



