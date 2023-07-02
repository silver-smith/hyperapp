import asyncio

from hyperapp.common.module import Module

from . import htypes


def python_object(piece, python_object_creg):
    fn = python_object_creg.invite(piece.function)
    event_loop = asyncio.new_event_loop()
    result = event_loop.run_until_complete(fn())
    return result


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.python_object_creg.register_actor(htypes.async_call.async_call, python_object, services.python_object_creg)
