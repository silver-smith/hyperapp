# Key-Value (string->string) storage backed by file directory.
# Each value stored in separate file, key mapped to file path

import os.path
import re
from ..common.util import is_list_inst
from ..common.packet_coders import packet_coders


class CacheRepository(object):

    def __init__( self, cache_dir, contents_encoding ):
        self._cache_dir = cache_dir
        self._contents_encoding = contents_encoding

    def _quote( self, name ):
        return re.sub(r'[/|"]', '-', name)

    def key2fpath( self, key ):
        assert is_list_inst(key, str), repr(key)
        return os.path.join(self._cache_dir, *tuple(map(self._quote, key)))
        
    def store_data( self, key, data ):
        fpath = self.key2fpath(key)
        dir = os.path.dirname(fpath)
        if not os.path.isdir(dir):
            os.makedirs(dir)
        with open(fpath, 'wb') as f:
            f.write(data)

    def load_data( self, key ):
        fpath = self.key2fpath(key)
        if not os.path.exists(fpath):
            return None
        with open(fpath, 'rb') as f:
            return f.read()

    def store_value( self, key, value, t ):
        if value is None: return
        data = packet_coders.encode(self._contents_encoding, value, t)
        self.store_data(key, data)

    def load_value( self, key, t ):
        data = self.load_data(key)
        if data is None:
            return None
        return packet_coders.decode(self._contents_encoding, data, t)
