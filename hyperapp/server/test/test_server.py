import unittest
from hyperapp.common.htypes import (
    tString,
    Field,
    RequestCmd,
    Interface,
    tServerPacket,
    tRequest,
#    register_iface,
    )
from hyperapp.common.htypes import IfaceRegistry
from hyperapp.common.packet import tAuxInfo, tPacket
from hyperapp.common.visual_rep import pprint
from hyperapp.server.request import RequestBase
import hyperapp.server.module as module_mod
from hyperapp.server.object import Object
from hyperapp.server.server import Server


test_iface = Interface('test_iface', commands=[
    RequestCmd('echo', [Field('test_param', tString)], [Field('test_result', tString)]),
    ])


class TestObject(Object):

    class_name = 'test_object'

    def process_request( self, request ):
        if request.command_id == 'echo':
            return self.run_command_echo(request)
        return Object.process_request(self, request)

    def run_command_echo( self, request ):
        return request.make_response_result(test_result=request.params.test_param + ' to you too')


class TestModule(module_mod.Module):

    name = 'test_module'

    def __init__( self ):
        module_mod.Module.__init__(self, self.name)

    def resolve( self, path ):
        objname = path.pop_str()
        if objname == TestObject.class_name:
            return TestObject()
        path.raise_not_found()

        
class ServerTest(unittest.TestCase):

    def test_simple_request( self ):
        iface_registry = IfaceRegistry()
        iface_registry.register(test_iface)
        module = TestModule()  # self-registering
        server = Server()
        request_data = tRequest.instantiate(
            iface='test_iface',
            path=[TestModule.name, TestObject.class_name],
            command_id='echo',
            params=test_iface.get_request_params_type('echo').instantiate(test_param='hello'),
            request_id='001',
            )
        request = RequestBase.from_data(None, None, iface_registry, request_data)
        aux_info, response = server.process_request(request)
        pprint(tAuxInfo, aux_info)
        pprint(tServerPacket, response)
        self.assertEqual('hello to you too', response.result.test_result)
