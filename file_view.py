# view file, splitted to lines; watch for it's size and follow it's end

import os.path
from object import Object, Element, Column


class File(Object):

    attributes = [
        Column('idx'),
        Column('line'),
        ]

    def __init__( self, fspath ):
        fspath = os.path.abspath(fspath)
        Object.__init__(self, '/file_view/' + fspath.lstrip('/'))
        self.fspath = fspath

    def get_all_elements( self ):
        return [Element(idx, line) for idx, line in enumerate(self._load_lines())]

    def _load_lines( self, ofs=0 ):
        with file(self._path) as f:
            if ofs:
                f.seek(ofs)
            return f.readlines()
