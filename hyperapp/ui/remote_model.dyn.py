from .services import (
    web,
    )
from .code.mark import mark


@mark.actor.formatter_creg
def format_remote_model(piece, peer_registry, peer_label_reg, format):
    model = web.summon(piece.model)
    remote_peer = peer_registry.invite(piece.remote_peer)
    model_title = format(model)
    remote_peer_label = peer_label_reg.get(remote_peer.piece) or repr(remote_peer)
    return f'{model_title} @ {remote_peer_label}'
