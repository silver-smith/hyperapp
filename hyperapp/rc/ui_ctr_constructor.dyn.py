import logging

log = logging.getLogger(__name__)

from . import htypes
from .services import (
    mosaic,
    )


class Constructor:

    def __init__(self, ctx, resource_module, module_res):
        self._ctx = ctx
        self._resource_module = resource_module
        self._module_res = module_res

    def _check_accepted_params(self, fn_info, accepted_params):
        unaccepted_params = fn_info.params.keys() - accepted_params
        if unaccepted_params:
            return f"Has unaccepted params: {', '.join(unaccepted_params)}; accepted are: {accepted_params}"
        return None

    def _make_attribute(self, name, base=None):
        return htypes.builtin.attribute(
            object=mosaic.put(self._module_res if base is None else base),
            attr_name=name,
        )
