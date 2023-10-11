import logging
import inspect

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.tracer import Tracer, value_type

log = logging.getLogger(__name__)


def call_function(import_recorders, fn_ref, trace_modules):
    tracer = Tracer(trace_modules)
    with tracer.tracing():
        value = pyobj_creg.invite(fn_ref)
        log.info("Resource value: %s", repr(value))

        if inspect.isgenerator(value):
            log.info("Expanding generator: %r", value)
            value = list(value)

    t = value_type(value)

    imports = set()

    return htypes.inspect.object_type_info(
        imports=list(sorted(imports)),
        t=mosaic.put(t),
        calls=tracer.calls,
        )
