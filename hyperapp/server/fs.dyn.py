from ..common.interface import fs as fs_types
from ..common.url import Url
from ..common.fs_service import FsService
from .command import command
from .object import Object
from .module import Module


MODULE_NAME = 'file'


class ServerFsService(Object):

    iface = fs_types.fs_service_iface
    class_name = 'service'

    def __init__(self, module):
        super().__init__()
        self._module = module
        self._fs_service = FsService(fs_types)

    def get_path(self):
        return self._module.make_path(self.class_name)

    def resolve(self, path):
        path.check_empty()
        return self

    @command('fetch_dir_contents')
    def command_fetch_dir_contents(self, request, host, fs_path, fetch_request):
        assert host == 'localhost', repr(host)  # remote hosts not supported
        chunk = self._fs_service.fetch_dir_contents(fs_path, fetch_request)
        return request.make_response_result(chunk=chunk)


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, MODULE_NAME)
        self._server = services.server
        self._fs_service = ServerFsService(self)
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
        all_rows = self.fetch_dir_contents(host, fs_path)
        chunk = rows2fetched_chunk('key', all_rows, fetch_request, fs_types.fs_dir_chunk)
