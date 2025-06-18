from .services import pyobj_creg
from .code.mark import mark


@mark.actor.cfg_item_creg
def resolve_feed_type_cfg_item(piece):
    model_t = pyobj_creg.invite(piece.model_t)
    return (model_t, piece)


@mark.actor.cfg_value_creg
def resolve_feed_type_cfg_value(piece, key, system, service_name):
    feed_type_creg = system.resolve_service('feed_type_creg')
    return feed_type_creg.invite(piece.feed_type)
