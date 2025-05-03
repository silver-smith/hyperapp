from . import htypes
from .services import (
    deduce_t,
    web,
    )
from .code.mark import mark


def real_model(model):
    if isinstance(model, htypes.model.remote_model):
        return web.summon(model.model)
    else:
        return model


def real_model_t(model):
    if isinstance(model, htypes.model.remote_model):
        _unused_real_model, model_t = web.summon_with_t(model.model)
        return model_t
    else:
        return deduce_t(model)


@mark.actor.formatter_creg
def format_remote_model(piece, peer_registry, peer_label_reg, format):
    model = web.summon(piece.model)
    remote_peer = peer_registry.invite(piece.remote_peer)
    model_title = format(model)
    remote_peer_label = peer_label_reg.get(remote_peer.piece) or repr(remote_peer)
    return f'{model_title} @ {remote_peer_label}'
