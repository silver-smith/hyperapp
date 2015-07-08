# view file, splitted to lines; watch for it's size and follow it's end

import os.path
from common.interface import Column
from common.interface.fs import file_iface
from object import ListObject


class File(ListObject):

    iface = file_iface
    proxy_id = 'list'

    columns = [
        Column('key', 'idx'),
        Column('line', 'line'),
        ]

    def __init__( self, path ):
        ListObject.__init__(self, path)
        self.fspath = os.path.abspath(path['fspath'])

    def get_commands( self ):
        return []

    def get_all_elements( self ):
        return [self.Element(idx, [idx, line]) for idx, line in enumerate(self._load_lines())]

    def _load_lines( self, ofs=0 ):
        with file(self.fspath) as f:
            if ofs:
                f.seek(ofs)
            return f.readlines()
