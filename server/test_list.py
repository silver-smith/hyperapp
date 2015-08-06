from common.interface import Command, Column, StringFieldHandle, IntFieldHandle, FormField, FormHandle
from common.interface.test_list import params_form_iface, test_list_iface
from util import path_part_to_str
from object import Object, ListObject
from module import Module, ModuleCommand


MODULE_NAME = 'test_list'
DEFAULT_SIZE = 10000
MAX_ROWS_RETURNED = 100


class ParamsForm(Object):

    iface = params_form_iface
    proxy_id = 'object'
    class_name = 'params'

    def get_path( self ):
        return module.make_path(self.class_name)

    def make_handle( self, key=0, size=DEFAULT_SIZE ):
        return FormHandle(self, [
            FormField('key', IntFieldHandle(key)),
            FormField('size', IntFieldHandle(size))])

    def get_commands( self ):
        return [Command('submit', 'Submit', 'Submit form', 'Return')]

    def process_request( self, request ):
        if request.command_id == 'submit':
            return self.run_command_submit(request)
        return Object.process_request(self, request)

    def run_command_submit( self, request ):
        print 'submitted: ', `request.params.key`, `request.params.size`
        object = TestList(request.params.size)
        handle = TestList.iface.ListHandle(object, request.params.key)
        return request.make_response(handle)


class TestList(ListObject):

    iface = test_list_iface
    proxy_id = 'list'
    class_name = 'list'

    @classmethod
    def resolve( cls, path ):
        size = path.pop_int()
        path.check_empty()
        return cls(size)

    def __init__( self, size=DEFAULT_SIZE ):
        ListObject.__init__(self)
        self.size = size

    def get_path( self ):
        return module.make_path(self.class_name, path_part_to_str(self.size))

    def get_commands( self ):
        return [Command('params', 'Params', 'Edit params', 'Return')]

    def process_request( self, request ):
        if request.command_id == 'params':
            return self.run_command_params(request)
        return ListObject.process_request(self, request)

    def run_command_params( self, request ):
        return request.make_response(ParamsForm().make_handle(size=self.size))

    def fetch_elements( self, sort_by_column, key, desc_count, asc_count ):
        assert key is None or isinstance(key, (int, long)), repr(key)
        if key is None:
            start = 0
        else:
            start = key + 1
        stop = min(self.size, start + min(asc_count, MAX_ROWS_RETURNED))
        elements = []
        for idx in xrange(start, stop):
            row = self.Row(idx, 'field1#%d' % idx, 'field2#%d' % idx, 'field3#%d' % idx)
            elements.append(self.Element(row))
        bof = True
        eof = stop >= self.size
        return (elements, bof, eof)
        ## start = min(self.size, from_key or 0)
        ## stop = min(self.size, start + max(count or 10, 10))
        ## print '--- fetch_elements', `self.size`, `count`, `from_key`, `start`, `stop`
        ## for idx in xrange(start, stop):
        ##     element = self.Element(idx, [str(idx), 'field1#%d' % idx, 'field2', 'field3'])
        ##     elements.append(element)
        ## has_more = stop < self.size
        ## return (elements, has_more)

    
class TestListModule(Module):

    def __init__( self ):
        Module.__init__(self, MODULE_NAME)

    def resolve( self, path ):
        class_name = path.pop_str()
        if class_name == ParamsForm.class_name:
            return ParamsForm()
        if class_name == TestList.class_name:
            return TestList.resolve(path)
        path.raise_not_found()

    def get_commands( self ):
        return [ModuleCommand('test_list', 'Test list', 'Open test list', 'Alt+T', self.name)]

    def run_command( self, request, command_id ):
        if command_id == 'test_list':
            return request.make_response_handle(TestList())
        return Module.run_command(self, request, command_id)


module = TestListModule()
