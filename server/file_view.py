# view file, splitted to lines; watch for it's size and follow it's end

import os.path
from object import ListObject, Element, Column
from iface import ListIface


class File(ListObject):

    iface = ListIface()
    view_id = 'list'

    columns = [
        Column('key', 'idx'),
        Column('line', 'line'),
        ]

    def __init__( self, fspath ):
        fspath = os.path.abspath(fspath)
        ListObject.__init__(self, '/file/' + fspath.lstrip('/'))
        self.fspath = fspath

    def get_commands( self ):
        return []

    def get_all_elements( self ):
        return [Element(idx, [idx, line]) for idx, line in enumerate(self._load_lines())]

    def _load_lines( self, ofs=0 ):
        with file(self.fspath) as f:
            if ofs:
                f.seek(ofs)
            return f.readlines()
