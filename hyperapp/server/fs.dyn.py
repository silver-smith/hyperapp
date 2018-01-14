import sys
import os.path
import stat
from operator import itemgetter
from ..common.interface import fs as fs_types
from ..common.url import Url
from .command import command
from .object import Object
from .module import Module
from .list_object import rows2fetched_chunk


MODULE_NAME = 'file'


class FsService(Object):

    iface = fs_types.fs_service_iface
    class_name = 'service'

    def __init__(self, module):
        super().__init__()
        self._module = module

    def get_path(self):
        return self._module.make_path(self.class_name)

    def resolve(self, path):
        path.check_empty()
        return self

    @command('fetch_dir_contents')
    def command_fetch_dir_contents(self, request):
        all_rows = self.fetch_dir_contents(request.params.host, request.params.fs_path)
        chunk = rows2fetched_chunk('key', all_rows, request.params.fetch_request, fs_types.fs_dir_chunk)
        return request.make_response_result(chunk=chunk)

    def fetch_dir_contents(self, host, fs_path):
        dir_path = '/' + '/'.join(fs_path)
        assert host == 'localhost', repr(host)  # remote hosts not supported
        dirs  = []
        files = []
        try:
            names = os.listdir(dir_path)
        except OSError:  # path may be invalid
            names = []
        for fname in names:
            fname = fsname2uni(fname)
            if fname[0] == '.': continue  # skip special and hidden names
            item_fs_path = os.path.join(dir_path, fname)
            finfo = self.get_file_info(fname, item_fs_path)
            if finfo['ftype'] == 'dir':
                dirs.append(finfo)
            else:
                files.append(finfo)
        return [fs_types.fs_dir_row(key=finfo['key'], ftype=finfo['ftype'], ftime=finfo['ftime'], fsize=finfo['fsize'])
                for finfo in sorted(dirs, key=itemgetter('key')) +
                             sorted(files, key=itemgetter('key'))]

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


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, MODULE_NAME)
        self._server = services.server
        self._fs_service = FsService(self)
        self._ref_storage = services.ref_storage
        self._management_ref_list = services.management_ref_list

    def init_phase3(self):
        fs_service_url = Url(fs_types.fs_service_iface, self._server.get_public_key(), self._fs_service.get_path())
        fs_service = fs_types.fs_service(service_url=fs_service_url.to_data())
        fs_service_ref = self._ref_storage.add_object(fs_types.fs_service, fs_service)
        fs = fs_types.fs_ref(
            fs_service_ref=fs_service_ref,
            host='localhost',
            path=['usr', 'share'],
            current_file_name='dpkg',
            )
        fs_ref = self._ref_storage.add_object(fs_types.fs_ref, fs)
        self._management_ref_list.add_ref('fs', fs_ref)

    def resolve(self, iface, path):
        name = path.pop_str()
        if name == self._fs_service.class_name:
            return self._fs_service.resolve(path)
        path.raise_not_found()


if sys.platform == 'win32':
    fs_encoding = sys.getfilesystemencoding()
else:
    fs_encoding = 'utf-8'

def fsname2uni(v):
    if type(v) is str:
        return v
    else:
       return str(v, fs_encoding)
