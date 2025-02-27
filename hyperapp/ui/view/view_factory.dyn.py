from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.directory import k_to_name


class ViewFactory:

    def __init__(self, k, ui_t_t, view_t, is_wrapper, view_ctx_params, system_fn):
        self._k = k
        self._ui_t_t = ui_t_t
        self._view_t = view_t
        self._is_wrapper = is_wrapper
        self._view_ctx_params = view_ctx_params
        self._system_fn = system_fn

    @property
    def k(self):
        return self._k

    def match_model(self, model_t, ui_t):
        if self._ui_t_t is None:
            return True
        if ui_t is None:
            return False
        return isinstance(ui_t, self._ui_t_t)

    @property
    def fn(self):
        return self._system_fn

    @property
    def item(self):
        return htypes.view_factory.item(
            k=mosaic.put(self._k),
            k_str=k_to_name(self._k),
            view_t=pyobj_creg.actor_to_ref(self._view_t),
            view_t_str=str(self._view_t),
            is_wrapper=self._is_wrapper,
            view_ctx_params=tuple(self._view_ctx_params),
            model_t=None,
            system_fn=mosaic.put(self._system_fn.piece),
            )


class ViewFactoryReg:

    def __init__(self, visualizer_reg, config):
        self._visualizer_reg = visualizer_reg
        self._config = config

    def __getitem__(self, k):
        return self._config[k]

    def values(self, model_t=None):
        if model_t is None:
            ui_t = None
        else:
            try:
                ui_t, unused_system_fn_ref = self._visualizer_reg(model_t)
            except KeyError:
                ui_t = None
        return [
            factory
            for factory in self._config.values()
            if factory.match_model(model_t, ui_t)
            ]


# d -> ViewFactory.
@mark.service
def view_factory_reg(config, visualizer_reg):
    return ViewFactoryReg(visualizer_reg, config)
