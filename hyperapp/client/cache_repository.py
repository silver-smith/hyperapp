# Key-Value (string->string) storage backed by file directory.
# Each value stored in separate file, key mapped to file path

import os.path
import re
from ..common.util import is_list_inst
from ..common.packet_coders import packet_coders


CACHE_DIR = os.path.expanduser('~/.cache/hyperapp/client')
CONTENTS_ENCODING = 'json_pretty'


class CacheRepository(object):

    def __init__( self ):
        pass

    def _quote( self, name ):
        return re.sub(r'[/|"]', '-', name)

    def key2fpath( self, key ):
        assert is_list_inst(key, str), repr(key)
        return os.path.join(CACHE_DIR, *tuple(map(self._quote, key)))
        
    def store_data( self, key, data ):
        fpath = self.key2fpath(key)
        dir = os.path.dirname(fpath)
        if not os.path.isdir(dir):
            os.makedirs(dir)
        with file(fpath, 'wb') as f:
            f.write(data)

    def load_data( self, key ):
        fpath = self.key2fpath(key)
        if not os.path.exists(fpath):
            return None
        with file(fpath, 'rb') as f:
            return f.read()

    def store_value( self, key, value, t ):
        if value is None: return
        data = packet_coders.encode(CONTENTS_ENCODING, value, t)
        self.store_data(key, data)

    def load_value( self, key, t ):
        data = self.load_data(key)
        if data is None:
            return None
        return packet_coders.decode(CONTENTS_ENCODING, data, t)


cache_repository = CacheRepository()
