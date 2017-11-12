from ..common.interface import hyper_ref as href_types
from .module import Module, ModuleCommand


MODULE_NAME = 'hyperref_test'


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, MODULE_NAME)

    def get_commands(self):
        return [
            ModuleCommand('test_href', 'Test href', 'Open test hyperref', None, self.name),
            ]

    def run_command(self, request, command_id):
        if command_id == 'test_href':
            href = href_types.href('sha256', b'test-fs-href')
            handle = href_types.href_redirect_handle('href_redirect', href)
            return request.make_response_handle(handle)
        return Module.run_command(self, request, command_id)
