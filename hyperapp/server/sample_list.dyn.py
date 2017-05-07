import logging
from ..common.htypes import Column
from ..common.interface import core as core_types
from ..common.interface import form as form_types
from ..common.interface import test_list as test_list_types
from .util import path_part_to_str
from .command import command
from .object import Object, ListObject
from .module import Module, ModuleCommand
from .form import intFieldHandle, formHandle

log = logging.getLogger(__name__)


MODULE_NAME = 'test_list'
DEFAULT_SIZE = 10000
MAX_ROWS_RETURNED = 100


class ParamsForm(Object):

    iface = test_list_types.params_form
    objimpl_id = 'proxy'
    class_name = 'params'

    def get_path(self):
        return module.make_path(self.class_name)

    def get_handle(self, request):
        return self.make_handle(request)  # todo: form data must be preserved somehow

    def make_handle(self, request, key=0, size=DEFAULT_SIZE):
        return formHandle(self.get(request), [
            form_types.form_field('key', intFieldHandle(key)),
            form_types.form_field('size', intFieldHandle(size)),
            ])

    @command('submit')
    def command_submit(self, request):
        log.info('submitted: key=%r size=%r', request.params.key, request.params.size)
        object = TestList(request.params.size)
        handle = TestList.ListHandle(object.get(request), key=request.params.key)
        return request.make_response_handle(handle)


class TestList(ListObject):

    iface = test_list_types.test_list
    objimpl_id = 'proxy_list'
    class_name = 'list'

    @classmethod
    def resolve(cls, path):
        size = path.pop_int()
        path.check_empty()
        return cls(size)

    def __init__(self, size=DEFAULT_SIZE):
        ListObject.__init__(self, core_types)
        self.size = size

    def get_path(self):
        return module.make_path(self.class_name, path_part_to_str(self.size))

    @command('params')
    def command_params(self, request):
        return request.make_response_handle(ParamsForm().make_handle(request, size=self.size))

    def fetch_elements(self, sort_column_id, from_key, direction, count):
        assert direction == 'asc', repr(direction)  # Descending direction is not yet supported
        assert from_key is None or isinstance(from_key, int), repr(from_key)
        if from_key is None:
            start = 0
        else:
            start = from_key + 1
        stop = min(self.size, start + min(count, MAX_ROWS_RETURNED))
        elements = []
        for idx in range(start, stop):
            row = self.Row(idx, 'field1#%d' % idx, 'field2#%d' % idx, 'field3#%d' % idx)
            elements.append(self.Element(row))
        bof = start == 0
        eof = stop >= self.size
        return self.Slice(sort_column_id, from_key, direction, elements, bof, eof)

    
class TestListModule(Module):

    def __init__(self):
        Module.__init__(self, MODULE_NAME)

    def resolve(self, iface, path):
        class_name = path.pop_str()
        if class_name == ParamsForm.class_name:
            return ParamsForm()
        if class_name == TestList.class_name:
            return TestList.resolve(path)
        path.raise_not_found()

    def get_commands(self):
        return [ModuleCommand('test_list', 'Test list', 'Open test list', 'Alt+T', self.name)]

    def run_command(self, request, command_id):
        if command_id == 'test_list':
            return request.make_response_object(TestList())
        return Module.run_command(self, request, command_id)


module = TestListModule()
