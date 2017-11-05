import sys
import os.path
import stat
from ..common.htypes import Column
from ..common.interface import core as core_types
from ..common.interface import fs as fs_types
from .command import command
from .object import Object, SmallListObject
from .module import Module, ModuleCommand

MODULE_NAME = 'file'


class FsObject(SmallListObject):

    def __init__(self, fspath):
        SmallListObject.__init__(self, core_types)
        self.fspath = os.path.abspath(fspath)

    def get_path(self):
        return this_module.make_path(self.fspath)


class File(FsObject):

    iface = fs_types.fs_file
    objimpl_id = 'proxy_list'
    default_sort_column_id = 'idx'

    def get_commands(self):
        return []

    def fetch_all_elements(self, request):
        return [self.Element(self.Row(idx, line)) for idx, line in enumerate(self._load_lines())]

    def _load_lines(self, ofs=0):
        with open(self.fspath) as f:
            if ofs:
                f.seek(ofs)
            return f.readlines()


class Dir(FsObject):

    iface = fs_types.fs_dir
    objimpl_id = 'proxy_list'
    categories = [['initial', 'fs']]

    def fetch_all_elements(self, request):
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
        def key(finfo):
            return finfo['key']
        return list(map(self.make_elt, sorted(dirs, key=key) + sorted(files, key=key)))

    def get_file_info(self, fname, fspath):
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
 
    def make_elt(self, finfo):
        row = self.Row(key=finfo['key'], ftype=finfo['ftype'], ftime=finfo['ftime'], fsize=finfo['fsize'])
        return self.Element(row, commands=[self.command_open])

    def get_handle(self, request):
        return self.CategorizedListHandle(self.get(request))

    @command('open', kind='element')
    def command_open(self, request):
        fname = request.params.element_key
        fspath = os.path.join(self.fspath, fname)
        return request.make_response_object(this_module.open(fspath))

    @command('parent')
    def command_parent(self, request):
        fspath = self.get_parent_dir()
        if fspath is None: return None
        key = os.path.basename(self.fspath)
        handle = self.CategorizedListHandle(this_module.open(fspath).get(request), key=key)
        return request.make_response_handle(handle)

    def get_parent_dir(self):
        dir = os.path.dirname(self.fspath)
        if dir == self.fspath:
            return None  # already root
        return dir


class FsService(Object):

    iface = fs_types.fs_service
    class_name = 'service'

    @classmethod
    def get_path(cls):
        return this_module.make_path(cls.class_name)


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, MODULE_NAME)

    def resolve(self, iface, path):
        fspath = path.pop_str()
        return self.open(fspath)

    def get_commands(self):
        return [ModuleCommand('home', 'Home', 'Open home directory', ['Alt+H'], self.name)]

    def run_command(self, request, command_id):
        if command_id == 'home':
            return request.make_response_object(self.open(os.path.expanduser('~')))
        return Module.run_command(self, request, command_id)

    def open(self, fspath):
        if os.path.isdir(fspath):
            return Dir(fspath)
        else:
            return File(fspath)


if sys.platform == 'win32':
    fs_encoding = sys.getfilesystemencoding()
else:
    fs_encoding = 'utf-8'

def fsname2uni(v):
    if type(v) is str:
        return v
    else:
       return str(v, fs_encoding)
