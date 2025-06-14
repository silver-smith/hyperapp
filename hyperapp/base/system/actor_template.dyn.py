from dataclasses import dataclass

from hyperapp.boot.htypes import Type

from . import htypes
from .services import (
    pyobj_creg,
    )


@dataclass
class ActorRequester:

    actor_t: Type

    def __str__(self):
        return f"Actor {self.actor_t.full_name}"


def resolve_actor_cfg_item(piece):
    t = pyobj_creg.invite(piece.t)
    return (t, piece)


def resolve_actor_cfg_value(piece, key, system, service_name):
    fn = pyobj_creg.invite(piece.function)
    return system.bind_services(fn, piece.service_params, requester=ActorRequester(key))


def actor_template_cfg_item_config():
    return {
        htypes.system.actor_template: resolve_actor_cfg_item,
        }


def actor_template_cfg_value_config():
    return {
        htypes.system.actor_template: resolve_actor_cfg_value,
        }
