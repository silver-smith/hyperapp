import inspect
import logging
from collections import defaultdict
from types import ModuleType


from hyperapp.common.htypes import HException

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.constants import RESOURCE_NAMES_ATTR, RESOURCE_CTR_ATTR

log = logging.getLogger(__name__)


def _enum_attributes(object):
    name_to_res_name = getattr(object, RESOURCE_NAMES_ATTR, {})
    name_to_ctr_list = getattr(object, RESOURCE_CTR_ATTR, {})
    for name in dir(object):
        if name.startswith('_'):
            continue
        resource_name = name_to_res_name.get(name)
        constructors = name_to_ctr_list.get(name, [])
        value = getattr(object, name)
        if not resource_name:
            if not hasattr(value, '__module__'):
                continue  # 'partial' does not have it; may be others too.
            if type(object) is ModuleType and value.__module__ != object.__name__:
                continue  # Skip functions imported from other modules.
        if not callable(value):
            yield htypes.inspect.attr(name, getattr(value, '__module__', None), resource_name, constructors)
            continue
        try:
            signature = inspect.signature(value)
        except ValueError as x:
            if 'no signature found for builtin type' in str(x):
                continue
            raise
        param_list = list(signature.parameters.keys())
        args = (name, value.__module__, resource_name, constructors, param_list)
        if inspect.isgeneratorfunction(value):
            yield htypes.inspect.generator_fn_attr(*args)
        else:
            yield htypes.inspect.fn_attr(*args)


def import_module(import_recorders, module_ref):
    log.info("Import module: %s", module_ref)

    recorder_dict = defaultdict(list)
    for rec in import_recorders:
        recorder = pyobj_creg.invite(rec.recorder)
        recorder.reset()
        recorder_dict[rec.module].append(recorder)

    try:
        module = pyobj_creg.invite(module_ref)
    except HException as x:
        attr_list = []
        error = mosaic.put(x)
    else:
        attr_list = [
            mosaic.put(attr) for attr
            in _enum_attributes(module)
            ]
        error = None

    module_to_imports = defaultdict(set)
    for module_name, recorder_list in recorder_dict.items():
        for recorder in recorder_list:
            module_to_imports[module_name] |= recorder.used_imports()
    log.info("Used imports: %s", module_to_imports)
    module_imports_list = [
        htypes.inspect.module_imports(module_name, list(sorted(imports)))
        for module_name, imports in module_to_imports.items()
        ]

    return htypes.inspect.imported_module_info(
        imports=module_imports_list,
        attr_list=attr_list,
        error=error,
        )
