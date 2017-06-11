from ..common.interface import core as core_types
from ..common.interface import exception_test as exception_test_types
from .command import command
from .object import SmallListObject
from .module import Module, ModuleCommand

MODULE_NAME = 'exception_test'


class TestObject(SmallListObject):

    iface = exception_test_types.test_object
    objimpl_id = 'proxy_list'
    class_name = 'test_object'

    @classmethod
    def resolve(cls, path):
        size = path.pop_int()
        path.check_empty()
        return cls(size)

    def __init__(self):
        SmallListObject.__init__(self, core_types)

    def get_path(self):
        return this_module.make_path(self.class_name)

    @command('run')
    def command_params(self, request):
        id = request.params.element_key

    @command('open')
    def command_params(self, request):
        id = request.params.element_key

    def fetch_all_elements(self, request):
        return [self.Element(self.Row(idx, line)) for idx, line in enumerate(self._load_lines())]

    
class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, MODULE_NAME)

    def resolve(self, iface, path):
        class_name = path.pop_str()
        if class_name == TestObject.class_name:
            return TestObject.resolve(path)
        path.raise_not_found()

    def get_commands(self):
        return [ModuleCommand('test_object', 'Test object', 'Open test object', 'Alt+E', self.name)]

    def run_command(self, request, command_id):
        if command_id == 'test_object':
            return request.make_response_object(TestObject())
        return Module.run_command(self, request, command_id)
