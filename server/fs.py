import sys
import os.path
import stat
from common.interface.fs import dir_iface
from common.interface import Command
from common.request import Element, Column
from object import ListObject
from module import Module, ModuleCommand
import file_view


MODULE_NAME = 'file'


class Dir(ListObject):

    iface = dir_iface
    proxy_id = 'list'
    view_id = 'list_narrower'

    columns = [
        Column('key', 'File Name'),
        Column('ftype', 'File type'),
        Column('ftime', 'Modification time'),
        Column('fsize', 'File size'),
        ]

    def __init__( self, path ):
        ListObject.__init__(self, path)
        self.fspath = os.path.abspath(path['fspath'])

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
        row = [finfo[column.id] for column in self.columns]
        return Element(finfo['key'], row, commands=self.elt_commands(finfo))

    def elt_commands( self, finfo ):
        if finfo['ftype'] == 'dir':
            return [Command('open', 'Open', 'Open directory')]
        else:
            return [Command('open', 'Open', 'Open file')]

    def process_request( self, request ):
        if request.command_id == 'open':
            fname = request.params.element_key
            fspath = os.path.join(self.fspath, fname)
            return request.make_response_object(module.open_fspath(fspath))
        if request.command_id == 'parent':
            fspath = self.get_parent_dir()
            if fspath is not None:
                return request.make_response_object(module.open_fspath(fspath))
        return ListObject.process_request(self, request)

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
        fspath = path.get('fspath')
        if fspath is not None:
            return self.open(path, fspath)
        return Module.resolve(self, path)

    def get_commands( self ):
        return [ModuleCommand('home', 'Home', 'Open home directory', 'Alt+H', self.name)]

    def run_command( self, request, command_id ):
        if command_id == 'home':
            return request.make_response_object(self.open_fspath(os.path.expanduser('~')))
        return Module.run_command(self, request, command_id)

    def open_fspath( self, fspath ):
        path = self.make_path(fspath=fspath)
        return self.open(path, fspath)

    def open( self, path, fspath ):
        if os.path.isdir(fspath):
            return Dir(path)
        else:
            return file_view.File(path)


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
