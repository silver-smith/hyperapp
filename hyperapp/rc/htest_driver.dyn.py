import asyncio
import logging
import inspect

from hyperapp.common.association_registry import Association
from hyperapp.common.resource_ctr import RESOURCE_MODULE_CTR_NAME

from . import htypes
from .services import (
    association_reg,
    mosaic,
    pyobj_creg,
    web,
    )
from .code.driver_recorders import ImportRecorders
from .code.tracer import Tracer, value_type
from .code.tested_imports import TestedObject

log = logging.getLogger(__name__)


def call_test(import_recorders, test_call_res, module_res, tested_units, tested_services, trace_modules, use_associations):
    tracer = Tracer(trace_modules)
    recorders = ImportRecorders(import_recorders)
    associations = [Association.from_piece(piece, web) for piece in use_associations]

    with association_reg.associations_registered(associations, override=True):
        with tracer.tracing():
            with recorders.recording():

                module = pyobj_creg.animate(module_res)
                for rec in tested_units:
                    code_module = pyobj_creg.invite(rec.value)
                    setattr(module.tested.code, rec.code_name, code_module)
                    obj = getattr(module, rec.code_name, None)
                    if obj and isinstance(obj, TestedObject) and obj.path == ('tested', 'code', rec.code_name):
                        setattr(module, rec.code_name, code_module)
                for rec in tested_services:
                    service = pyobj_creg.invite(rec.value)
                    setattr(module.tested.services, rec.name, service)
                    obj = getattr(module, rec.name, None)
                    if obj and isinstance(obj, TestedObject) and obj.path == ('tested', 'services', rec.name):
                        setattr(module, rec.name, service)

                value = pyobj_creg.animate(test_call_res)

                if inspect.isgenerator(value):
                    log.info("Expanding generator: %r", value)
                    value = list(value)

                if inspect.iscoroutine(value):
                    log.info("Expanding coroutine: %r", value)
                    value = asyncio.run(value)

            log.info("Resource value: %s", repr(value))

    t = value_type(value)

    module_ctrs_list = []
    for rec in tested_units:
        code_module = pyobj_creg.invite(rec.value)
        constructors = getattr(code_module, RESOURCE_MODULE_CTR_NAME, [])
        module_ctrs = htypes.inspect.module_constructors(rec.name, tuple(constructors))
        module_ctrs_list.append(module_ctrs)

    return htypes.inspect.object_type_info(
        imports=recorders.module_imports_list,
        t=mosaic.put(t),
        calls=tracer.calls,
        tested_constructors=tuple(module_ctrs_list),
        )
