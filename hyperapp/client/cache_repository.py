# Key-Value (string->string) storage backed by file directory.
# Each value stored in separate file, key mapped to file path

import os.path
import string
import logging
import re
from ..common.util import is_list_inst
from ..common.htypes.packet_coders import packet_coders


log = logging.getLogger(__name__)


ALLOWED_CHARS = string.ascii_letters + string.digits + '_.-'


class CacheRepository(object):

    allowed_chars = ALLOWED_CHARS

    def __init__(self, cache_dir, contents_encoding, file_ext):
        self._cache_dir = cache_dir
        self._contents_encoding = contents_encoding
        self._file_ext = file_ext

    @property
    def allowed_chars_pattern(self):
        return self.allowed_chars.replace('.', r'\.').replace('-', r'\-')

    def _check_name(self, name):
        pattern = r'^[%s]+$' % self.allowed_chars_pattern
        if not re.match(pattern, name):
            raise RuntimeError('Only these chars are allowed: %s, but got: %s' % (self.allowed_chars, name))
        return name

    def _key2fpath(self, key):
        assert is_list_inst(key, str), repr(key)
        return os.path.join(self._cache_dir, *tuple(map(self._check_name, key))) + self._file_ext
        
    def _store_data(self, key, data):
        fpath = self._key2fpath(key)
        dir = os.path.dirname(fpath)
        if not os.path.isdir(dir):
            os.makedirs(dir)
        with open(fpath, 'wb') as f:
            f.write(data)

    def _load_data(self, key):
        fpath = self._key2fpath(key)
        if not os.path.exists(fpath):
            return None
        with open(fpath, 'rb') as f:
            return f.read()

    def store_value(self, key, value, t):
        if value is None: return
        data = packet_coders.encode(self._contents_encoding, value, t)
        self._store_data(key, data)

    def load_value(self, key, t):
        data = self._load_data(key)
        if data is None:
            return None
        return packet_coders.decode(self._contents_encoding, data, t)
