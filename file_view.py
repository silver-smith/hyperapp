# view file, splitted to lines; watch for it's size and follow it's end

import os.path
from object import Object, Element, Column


class File(Object):

    columns = [
        Column('key'),
        Column('line'),
        ]

    def __init__( self, fspath ):
        fspath = os.path.abspath(fspath)
        Object.__init__(self, '/file/' + fspath.lstrip('/'))
        self.fspath = fspath

    def dir_commands( self ):
        return []

    def get_all_elements( self ):
        return [Element(idx, [idx, line]) for idx, line in enumerate(self._load_lines())]

    def _load_lines( self, ofs=0 ):
        with file(self.fspath) as f:
            if ofs:
                f.seek(ofs)
            return f.readlines()
