from hyperapp.boot.ref import make_ref

from . import htypes
from .services import (
    web,
    )
from .code.mark import mark


def _msg_item(format, id, message):
    if len(message.msg_bundle.roots) == 1:
        msg = web.summon(message.msg_bundle.roots[0])
        msg_title = format(msg)
    else:
        msg_title = f"{len(message.msg_bundle.roots)} roots"
    return htypes.transport_log_model.item(
        id=id,
        dt=message.dt,
        direction=message.direction,
        transport_name=message.transport_name,
        msg_title=msg_title,
        msg_bundle=message.msg_bundle,
        transport_bundle=message.transport_bundle,
        transport_size=message.transport_size,
        )


@mark.model(key='id')
def transport_log_model(piece, transport_log, format):
    return [
        _msg_item(format, id, message)
        for id, message
        in transport_log.messages.items()
        ]


def _bundle_info_model(name, bundle):
    return htypes.bundle_info.model(
        bundle_name=name,
        roots=bundle.roots,
        associations=bundle.associations,
        capsules=tuple(make_ref(capsule) for capsule in bundle.capsule_list),
        )


@mark.command
def message(piece, current_item):
    bundle = current_item.msg_bundle
    if len(bundle.roots) != 1:
        log.warning("Can not open message roots: It has %d roots", len(bundle.roots))
        return
    return htypes.data_browser.record_view(
        data=bundle.roots[0],
        )


@mark.command
def message_bundle(piece, current_item):
    return _bundle_info_model(
        name=f"{current_item.transport_name}.{current_item.id}.{current_item.direction}.msg",
        bundle=current_item.msg_bundle,
        )


@mark.command
def transport_bundle(piece, current_item):
    return _bundle_info_model(
        name=f"{current_item.transport_name}.{current_item.id}.{current_item.direction}.transport",
        bundle=current_item.transport_bundle,
        )


@mark.global_command
def open_transport_log():
    return htypes.transport_log_model.model()
