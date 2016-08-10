# test for returning non-proxy object to client, text object

import os.path
from .. common.htypes import tObjHandle, make_meta_type_registry, builtin_type_registry
from .. common.type_module import load_types_from_yaml_file
from .module import Module, ModuleCommand

text_object_types = load_types_from_yaml_file(
    make_meta_type_registry(), builtin_type_registry(),
    os.path.abspath(os.path.join(os.path.dirname(__file__), 'text_object.types.yaml')))


MODULE_NAME = 'test_text_object'


sample_text = '''
Lorem Ipsum is simply dummy text of the printing and typesetting industry.
Lorem Ipsum has been the industry's standard dummy text ever since the 1500s,
when an unknown printer took a galley of type and scrambled it to make a type specimen book.
It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged.
It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages,
and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.
'''


class TestTextObjectModule(Module):

    def __init__( self ):
        Module.__init__(self, MODULE_NAME)

    def get_commands( self ):
        return [ModuleCommand('get_text_obj', 'Get text', 'Produce test text object', None, self.name)]

    def run_command( self, request, command_id ):
        if command_id == 'get_text_obj':
            object = text_object_types.text_object('text', sample_text)
            handle = tObjHandle('text_view', object)
            return request.make_response_handle(handle)
        return Module.run_command(self, request, command_id)


module = TestTextObjectModule()
