import inspect
import logging
from types import ModuleType


from hyperapp.common.htypes import HException
from hyperapp.common.resource_ctr import RESOURCE_ATTR_CTR_NAME

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.driver_recorders import ImportRecorders

log = logging.getLogger(__name__)


def _enum_attributes(object):
    name_to_ctr_list = getattr(object, RESOURCE_ATTR_CTR_NAME, {})
    for name in dir(object):
        if name.startswith('_'):
            continue
        constructors = tuple(name_to_ctr_list.get(name, []))
        value = getattr(object, name)
        if not hasattr(value, '__module__'):
            continue  # 'partial' does not have it; may be others too.
        if type(object) is ModuleType and value.__module__ != object.__name__:
            continue  # Skip functions imported from other modules.
        if not callable(value):
            yield htypes.inspect.attr(name, getattr(value, '__module__', None), constructors)
            continue
        try:
            signature = inspect.signature(value)
        except ValueError as x:
            if 'no signature found for builtin type' in str(x):
                continue
            raise
        param_list = tuple(signature.parameters.keys())
        args = (name, value.__module__, constructors, param_list)
        if inspect.isgeneratorfunction(value):
            yield htypes.inspect.generator_fn_attr(*args)
        elif inspect.isclass(value):
            yield htypes.inspect.class_attr(*args)
        else:
            yield htypes.inspect.fn_attr(*args)


def import_module(import_recorders, module_ref):
    log.info("Import module: %s", module_ref)

    recorders = ImportRecorders(import_recorders)
    try:
        with recorders.recording():
            module = pyobj_creg.invite(module_ref)
    except HException as x:
        attr_list = ()
        error = mosaic.put(x)
    else:
        attr_list = tuple(
            mosaic.put(attr) for attr
            in _enum_attributes(module)
            )
        error = None

    return htypes.inspect.imported_module_info(
        imports=recorders.module_imports_list,
        attr_list=attr_list,
        error=error,
        )
