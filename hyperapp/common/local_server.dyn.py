from pathlib import Path

from hyperapp.common.module import Module


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        services.local_server_ref = services.file_bundle(Path.home() / '.local/share/hyperapp/server-ref.json')
