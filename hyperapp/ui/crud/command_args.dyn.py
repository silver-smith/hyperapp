from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )


def args_t_dict_to_tuple(args):
    return tuple(
        htypes.command.arg_t(
            name=name,
            t=pyobj_creg.actor_to_ref(t),
            )
        for name, t in args.items()
        )


def args_t_tuple_to_dict(args):
    return {
        arg.name: pyobj_creg.invite(arg.t)
        for arg in args
        }


def args_dict_to_tuple(args):
    if args is None:
        return ()
    return tuple(
        htypes.command.arg(
            name=name,
            value=mosaic.put(value),
            )
        for name, value in args.items()
        )


def args_tuple_to_dict(args):
    return {
        arg.name: web.summon(arg.value)
        for arg in args
        }
