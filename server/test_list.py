from common.interface import Command, Column
from common.interface.test_list import test_list_iface
from object import ListObject
from module import Module, ModuleCommand


MODULE_NAME = 'test_list'


class TestList(ListObject):

    iface = test_list_iface
    proxy_id = 'list'

    columns = [
        Column('key'),
        Column('field_1', 'Field #1'),
        Column('field_2', 'Field #2'),
        Column('field_3', 'Field #3'),
        ]

    def __init__( self ):
        ListObject.__init__(self)

    def get_path( self ):
        return module.make_path()

    def get_elements( self, count=None, from_key=None ):
        start = from_key or 0
        stop = start + max(count or 10, 10)
        elements = [self.Element(idx, [str(idx), 'field1#%d' % idx, 'field2', 'field3'])
                    for idx in xrange(start, stop)]
        has_more = True
        return (elements, has_more)

    
class TestListModule(Module):

    def __init__( self ):
        Module.__init__(self, MODULE_NAME)

    def resolve( self, path ):
        path.check_empty()
        return TestList()

    def get_commands( self ):
        return [ModuleCommand('test_list', 'Test list', 'Open test lisg', 'Alt+T', self.name)]

    def run_command( self, request, command_id ):
        if command_id == 'test_list':
            return request.make_response_handle(TestList())
        return Module.run_command(self, request, command_id)


module = TestListModule()
