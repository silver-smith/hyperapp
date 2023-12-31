from hyperapp.common.code_registry import CodeRegistry

from .services import (
    association_reg,
    mark,
    mosaic,
    pyobj_creg,
    types,
    )


@mark.service
def ui_adapter_creg():
    registry = CodeRegistry('ui_adapter', mosaic, types)
    registry.init_registries(association_reg, pyobj_creg)
    return registry
