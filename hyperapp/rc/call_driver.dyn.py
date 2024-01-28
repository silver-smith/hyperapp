import asyncio
import logging
import inspect

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.driver_recorders import ImportRecorders
from .code.tracer import Tracer, value_type

log = logging.getLogger(__name__)


def call_function(import_recorders, call_result_ref, trace_modules):
    tracer = Tracer(trace_modules)
    recorders = ImportRecorders(import_recorders)
    with tracer.tracing():
        with recorders.recording():

            value = pyobj_creg.invite(call_result_ref)

            if inspect.isgenerator(value):
                log.info("Expanding generator: %r", value)
                value = list(value)

            if inspect.iscoroutine(value):
                log.info("Expanding coroutine: %r", value)
                value = asyncio.run(value)

            log.info("Resource value: %s", repr(value))

    t = value_type(value)

    return htypes.inspect.object_type_info(
        imports=recorders.module_imports_list,
        t=mosaic.put(t),
        calls=tracer.calls,
        )
