import logging

from hyperapp.common.htypes.deduce_value_type import deduce_value_type
from hyperapp.common.module import Module

from . import htypes

log = logging.getLogger(__name__)


def factory(data, resolve_name):
    fn_ref = resolve_name(data['function'])
    return htypes.map_service.map_service(fn_ref)


def map_piece_to_service(mosaic, request, piece, service):
    if isinstance(service, htypes.map_service.record_service):
        identity = request.receiver_identity
        peer_ref = mosaic.put(identity.peer.piece)
        get_fn = htypes.attribute.attribute(
            object_ref=mosaic.put(piece),
            attr_name='get',
            )
        return htypes.service.record_service(
            peer_ref=peer_ref,
            servant_fn_ref=mosaic.put(get_fn),
            dir_list=service.dir_list,
            command_ref_list=service.command_ref_list,
            )
    raise runtime_error(f"Unsupported service type for {piece}: {service}")


def python_object(piece, mosaic, python_object_creg, piece_service_registry):
    fn = python_object_creg.invite(piece.fn_ref)

    def inner(request, *args, **kw):
        log.info("Map service inner: %s, %s/%s", request, args, kw)
        result = fn(request, *args, **kw)
        if result is None:
            return result
        t = deduce_value_type(result)
        try:
            service = piece_service_registry[t]
        except KeyError:
            return result
        return map_piece_to_service(mosaic, request, result, service)

    return inner


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.piece_service_registry = {}  # piece_t -> map_service.service instance

        services.resource_type_reg['map_service'] = services.resource_type_factory(htypes.map_service.map_service)
        services.python_object_creg.register_actor(
            htypes.map_service.map_service, python_object, services.mosaic, services.python_object_creg, services.piece_service_registry)
