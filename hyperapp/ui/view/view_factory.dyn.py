from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.directory import d_to_name


class ViewFactory:

    def __init__(self, d, view_t, is_wrapper, view_ctx_params, system_fn):
        self._d = d
        self._view_t = view_t
        self._is_wrapper = is_wrapper
        self._view_ctx_params = view_ctx_params
        self._system_fn = system_fn

    @property
    def d(self):
        return self._d

    @property
    def item(self):
        return htypes.view_factory.item(
            d=mosaic.put(self._d),
            d_str=d_to_name(self._d),
            view_t=pyobj_creg.actor_to_ref(self._view_t),
            view_t_str=str(self._view_t),
            is_wrapper=self._is_wrapper,
            view_ctx_params=tuple(self._view_ctx_params),
            system_fn=mosaic.put(self._system_fn.piece),
            )


# d -> ViewFactory.
@mark.service
def view_factory_reg(config):
    return config
