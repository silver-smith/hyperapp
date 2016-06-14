import sys
import os.path
import logging
import asyncio
import unittest
from hyperapp.common.htypes import (
    tClientPacket,
    tRequest,
    IfaceRegistry,
    )
from hyperapp.common.endpoint import Url
from hyperapp.common.visual_rep import pprint
from hyperapp.client.request import Request
from hyperapp.client.server import Server
from hyperapp.common.interface.server_management import server_management_iface
# self-registering transports:
import hyperapp.client.tcp_transport
import hyperapp.client.encrypted_transport


class RealRequestTest(unittest.TestCase):

    def setUp( self ):
        self.iface_registry = IfaceRegistry()
        self.iface_registry.register(server_management_iface)

    def test_get_request( self ):
        loop = asyncio.get_event_loop()
        loop.set_debug(True)
        loop.run_until_complete(self.run_get_request())

    @asyncio.coroutine
    def run_get_request( self ):
        url = Url.from_str(self.iface_registry, open(os.path.expanduser('~/tmp/url')).read())
        request = Request(
            iface=url.iface,
            path=url.path,
            command_id='get',
            request_id='test-001',
            params=url.iface.get_request_params_type('get')(),
            )
        pprint(tClientPacket, request.to_data())
        server = Server.from_endpoint(url.endpoint)
        response = yield from (asyncio.wait_for(server.execute_request(request), timeout=0.5))
        assert 0
