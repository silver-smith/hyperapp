import sys
import os.path
import stat
from object import ListObject, Command, Element, Column
from module import Module, ModuleCommand
import file_view


MODULE_NAME = 'file'


class Dir(ListObject):

    columns = [
        Column('key', 'File Name'),
        Column('ftype', 'File type'),
        Column('ftime', 'Modification time'),
        Column('fsize', 'File size'),
        ]

    def __init__( self, fspath ):
        fspath = os.path.abspath(fspath)
        ListObject.__init__(self, '/fs/' + fspath.lstrip('/'))
        self.fspath = fspath

    def get_all_elements( self ):
        dirs  = []
        files = []
        try:
            names = os.listdir(self.fspath)
        except OSError:  # path may be invalid
            names = []
        for fname in names:
            fname = fsname2uni(fname)
            if fname[0] == '.': continue  # skip special and hidden names
            fspath = os.path.join(self.fspath, fname)
            finfo = self.get_file_info(fname, fspath)
            if finfo['ftype'] == 'dir':
                dirs.append(finfo)
            else:
                files.append(finfo)
        def key( finfo ):
            return finfo['key']
        return map(self.make_elt, sorted(dirs, key=key) + sorted(files, key=key))

    def get_file_info( self, fname, fspath ):
        s = os.stat(fspath)
        return dict(
            key=fname,
            ftype='dir' if os.path.isdir(fspath) else 'file',
            ftime=s[stat.ST_MTIME],
            fsize=s[stat.ST_SIZE],
            )
 
    def make_elt( self, finfo ):
        row = [finfo[column.id] for column in self.columns]
        return Element(finfo['key'], row, commands=self.elt_commands(finfo))

    def elt_commands( self, finfo ):
        if finfo['ftype'] == 'dir':
            return [Command('open', 'Open', 'Open directory')]
        else:
            return [Command('open', 'Open', 'Open file')]

    def run_element_command( self, command_id, element_key ):
        if command_id == 'open':
            elt_fname = element_key
            fspath = os.path.join(self.fspath, elt_fname)
            if os.path.isdir(fspath):
                return Dir(fspath)
            else:
                return file_view.File(fspath)
        assert False, repr(command_id)  # Unexpected command_id

    def run_command( self, command_id ):
        assert command_id == 'parent', repr(command_id)
        fspath = self.get_parent_dir()
        if fspath is not None:
            return Dir(fspath)

    def get_parent_dir( self ):
        dir = os.path.dirname(self.fspath)
        if dir == self.fspath:
            return None  # already root
        return dir

    def get_commands( self ):
        return [Command('parent', 'Open parent', 'Open parent directory', 'Ctrl+Backspace')]


class FileModule(Module):

    def __init__( self ):
        Module.__init__(self, MODULE_NAME)

    def get_commands( self ):
        return [ModuleCommand('home', 'Home', 'Open home directory', 'Ctrl+F', self.name)]

    def run_command( self, command_id ):
        if command_id == 'home':
            return Dir(os.path.expanduser('~'))
        assert False, repr(command_id)  # Unsupported command


if sys.platform == 'win32':
    fs_encoding = sys.getfilesystemencoding()
else:
    fs_encoding = 'utf-8'

def fsname2uni( v ):
    if type(v) is unicode:
        return v
    else:
       return unicode(v, fs_encoding)


module = FileModule()
