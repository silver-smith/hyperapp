import sys
import os.path
import stat
from ..common.interface import Command, Column
from ..common.interface.fs import file_iface, dir_iface
from .object import SmallListObject
from .module import Module, ModuleCommand


MODULE_NAME = 'file'


class FsObject(SmallListObject):

    def __init__( self, fspath ):
        SmallListObject.__init__(self)
        self.fspath = os.path.abspath(fspath)

    def get_path( self ):
        return module.make_path(self.fspath)


class File(FsObject):

    iface = file_iface
    objimpl_id = 'list'
    default_sort_column_id = 'idx'

    def get_commands( self ):
        return []

    def fetch_all_elements( self ):
        return [self.Element(self.Row(idx, line)) for idx, line in enumerate(self._load_lines())]

    def _load_lines( self, ofs=0 ):
        with file(self.fspath) as f:
            if ofs:
                f.seek(ofs)
            return f.readlines()


class Dir(FsObject):

    iface = dir_iface
    objimpl_id = 'list'

    def fetch_all_elements( self ):
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
        try:
            s = os.stat(fspath)
        except OSError:
            return dict(
                key=fname,
                ftype='file',
                ftime=0,
                fsize=0)
        return dict(
            key=fname,
            ftype='dir' if os.path.isdir(fspath) else 'file',
            ftime=s[stat.ST_MTIME],
            fsize=s[stat.ST_SIZE],
            )
 
    def make_elt( self, finfo ):
        row = self.Row(key=finfo['key'], ftype=finfo['ftype'], ftime=finfo['ftime'], fsize=finfo['fsize'])
        return self.Element(row, commands=self.elt_commands(finfo))

    def elt_commands( self, finfo ):
        if finfo['ftype'] == 'dir':
            return [Command('open', 'Open', 'Open directory')]
        else:
            return [Command('open', 'Open', 'Open file')]

    def get_handle( self ):
        return self.ListNarrowerHandle(self.get(), 'key')

    def process_request( self, request ):
        if request.command_id == 'open':
            fname = request.params.element_key
            fspath = os.path.join(self.fspath, fname)
            return request.make_response_handle(module.open(fspath))
        if request.command_id == 'parent':
            fspath = self.get_parent_dir()
            if fspath is None: return None
            key = os.path.basename(self.fspath)
            handle = self.ListNarrowerHandle(module.open(fspath).get(), 'key', key)
            return request.make_response(handle)
        return SmallListObject.process_request(self, request)

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

    def resolve( self, path ):
        fspath = path.pop_str()
        return self.open(fspath)

    def get_commands( self ):
        return [ModuleCommand('home', 'Home', 'Open home directory', 'Alt+H', self.name)]

    def run_command( self, request, command_id ):
        if command_id == 'home':
            return request.make_response_handle(self.open(os.path.expanduser('~')))
        return Module.run_command(self, request, command_id)

    def open( self, fspath ):
        if os.path.isdir(fspath):
            return Dir(fspath)
        else:
            return File(fspath)


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
