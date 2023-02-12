from dateutil import parser
from datetime import datetime

TYPE_IMAGE = "image"
TYPE_VIDEO = "video"
TYPE_OTHER = "other"
TYPE_UNKNOWN = "unknown"

TYPE_DICTIONARY = {
    'png': TYPE_IMAGE,
    'jpg': TYPE_IMAGE,
    'jpeg': TYPE_IMAGE,
    'bmp': TYPE_IMAGE,
    'gif': TYPE_IMAGE,
    'tif': TYPE_IMAGE,
    'cr2': TYPE_IMAGE,
    'avi': TYPE_VIDEO,
    'mpg': TYPE_VIDEO,
    'mp4': TYPE_VIDEO,
    'mov': TYPE_VIDEO,
    'mts': TYPE_VIDEO,
    '3gp': TYPE_VIDEO,
    'm2t': TYPE_VIDEO,
    'db': TYPE_OTHER,
    'ini': TYPE_OTHER,
    'sh': TYPE_OTHER,
    'xmp': TYPE_OTHER,
}


class File(object):
    name = None
    relative_path = None
    size = None
    original_path = None
    file_type = None
    download_source = None

    def __str__(self):
        return (self.name + ' : ' + self.original_path + ' size:(%d)') % self.size

    def convert_time_string(self, time_string):
        if time_string is None:
            return None
        # Example format: u'2013:02:14 12:31:58'
        try:
            t = datetime.strptime(time_string, '%Y:%m:%d %H:%M:%S')
            if t is not None:
                return t
        except Exception as e:
            print('Exception converting time string (%s) :: %s' % (time_string, e.message))
        try:
            t = parser.parse(time_string)
            if t is not None:
                return t
        except Exception as e:
            print('Exception converting time string (%s) :: %s' % (time_string, e.message))
        return None

    @classmethod
    def type_from_extension(cls, extension):
        if extension is None:
            return TYPE_OTHER
        extension = extension.lower().lstrip('.')
        if extension in TYPE_DICTIONARY:
            return TYPE_DICTIONARY[extension]
        # What extension is this?
        return TYPE_UNKNOWN
