import logging
import threading
from types import SimpleNamespace

from hyperapp.common.htypes import (
    field_mt,
    record_mt,
    request_mt,
    interface_mt,
    name_wrapped_mt,
    bundle_t,
    list_service_t,
    )
from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common.module import Module

from . import htypes
from .column import Column
from .simple_list_object import SimpleListObject

log = logging.getLogger(__name__)


def list_interface_ref(mosaic, list_ot, name):
    field_list = [
        field_mt(column.id, column.type_ref)
        for column in list_ot.column_list
        ]
    row_mt = record_mt(None, field_list)
    row_ref = mosaic.put(row_mt)
    named_row_ref = mosaic.put(name_wrapped_mt(f'{name}_row', row_ref))

    rows_field = field_mt('rows', named_row_ref)
    get_method_ref = mosaic.put(request_mt('get', [], [rows_field]))
    interface_ref = mosaic.put(interface_mt(None, [get_method_ref]))
    named_interface_ref = mosaic.put(name_wrapped_mt(f'{name}_interface', interface_ref))
    return named_interface_ref


class TestListService(SimpleListObject):

    @classmethod
    async def from_piece(cls, piece, my_identity, mosaic, async_rpc_endpoint, async_rpc_proxy):
        list_ot = mosaic.resolve_ref(piece.type_ref).value
        interface_ref = list_interface_ref(mosaic, list_ot, 'test_list_service')
        service = htypes.rpc.endpoint(
            peer_ref=piece.peer_ref,
            iface_ref=interface_ref,
            object_id=piece.object_id,
            )
        rpc_endpoint = async_rpc_endpoint()
        proxy = async_rpc_proxy(my_identity, rpc_endpoint, service)
        return cls(mosaic, list_ot, piece.peer_ref, piece.object_id, piece.key_field, proxy)

    def __init__(self, mosaic, list_ot, peer_ref, object_id, key_field, proxy):
        super().__init__()
        self._mosaic = mosaic
        self._list_ot = list_ot
        self._peer_ref = peer_ref
        self._object_id = object_id
        self._key_field = key_field
        self._proxy = proxy

    @property
    def title(self):
        return f"List service: {self._object_id}"

    @property
    def piece(self):
        list_ot_ref = self._mosaic.put(self._list_ot)
        return list_service_t(
            type_ref=list_ot_ref,
            peer_ref=self._peer_ref,
            object_id=self._object_id,
            )

    @property
    def columns(self):
        return [
            Column(name, is_key=(name == self._service.key_field))
            for name, t in self._service_type.fields.items()
            ]

    async def get_all_items(self):
        row_list = await self._proxy.get()
        return [row for row in row_list]


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)

        self._object_registry = services.object_registry
        self._async_rpc_endpoint = services.async_rpc_endpoint

        list_service_bundle = packet_coders.decode('cdr', config['list_service_bundle_cdr'], bundle_t)
        services.unbundler.register_bundle(list_service_bundle)
        self._list_service_ref = list_service_bundle.roots[0]

        self._my_identity = services.generate_rsa_identity(fast=True)

        services.object_registry.register_actor(
            list_service_t, TestListService.from_piece,
            services.mosaic, services.async_rpc_endpoint, services.async_rpc_proxy)

    async def async_init(self, services):
        log.info("List service async run:")
        try:
            object = await self._object_registry.invite(self._list_service_ref, self._my_identity)

            rows = await object.get_all_items()
            log.info("Returned rows: %s", rows)
        except Exception as x:
            log.exception("List service async run is failed:")
        log.info("List service async run: done.")
