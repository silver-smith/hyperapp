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


@mark.global_command
def open_transport_log():
    return htypes.transport_log_model.model()
