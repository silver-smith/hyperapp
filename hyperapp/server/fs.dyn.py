from hyperapp.common.module import Module
from . import htypes
from .fs_service_impl import FsServiceImpl


MODULE_NAME = 'fs'
FS_SERVICE_ID = 'fs'


class FsService(object):

    def __init__(self):
        self._impl = FsServiceImpl()

    def rpc_fetch_dir_contents(self, request, host, fs_path, fetch_request):
        assert host == 'localhost', repr(host)  # remote hosts not supported
        chunk = self._impl.fetch_dir_contents(fs_path, fetch_request)
        return request.make_response_result(chunk=chunk)


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        self._init_fs_service(services)

    def _init_fs_service(self, services):
        iface_type_ref = services.type_resolver.reverse_resolve(htypes.fs.fs_service_iface)
        service = htypes.hyper_ref.service(FS_SERVICE_ID, iface_type_ref)
        service_ref = services.ref_registry.register_object(service)
        services.service_registry.register(service_ref, FsService)

        fs = htypes.fs.fs(
            fs_service_ref=service_ref,
            host='localhost',
            path=['usr', 'share'],
            current_file_name='dpkg',
            )
        fs_ref = services.ref_registry.register_object(fs)
        services.management_ref_list.add_ref('fs', fs_ref)
