from . import htypes
from .services import (
    deduce_t,
    mosaic,
    pyobj_creg,
    )
from .code.mark import mark
from .code.directory import k_to_name


class ViewFactory:

    def __init__(self, visualizer_reg, k, model_t, ui_t_t, view_t, is_wrapper, view_ctx_params, system_fn):
        assert not (model_t is not None and ui_t_t is not None)  # Not both.
        self._visualizer_reg = visualizer_reg
        self._k = k
        self._model_t = model_t
        self._ui_t_t = ui_t_t
        self._view_t = view_t
        self._is_wrapper = is_wrapper
        self._view_ctx_params = view_ctx_params
        self._system_fn = system_fn

    @property
    def k(self):
        return self._k

    def match_model(self, model_t, ui_t):
        if self._model_t is not None:
            return model_t is self._model_t
        if self._ui_t_t is not None:
            return isinstance(ui_t, self._ui_t_t)
        return True

    def call(self, ctx):
        if self._ui_t_t is not None:
            model_t = deduce_t(ctx.model)
            ui_t, system_fn_ref = self._visualizer_reg(model_t)
            fn_ctx = ctx.clone_with(
                piece=ui_t,
                system_fn_ref=system_fn_ref,
            )
        else:
            fn_ctx = ctx
        return self._system_fn.call(fn_ctx)

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

    def get_item_list(self, model):
        return [self.item]


class ViewMultiFactory:

    def __init__(self, visualizer_reg, model_t, ui_t_t, list_fn):
        assert not (model_t is not None and ui_t_t is not None)  # Not both.
        self._visualizer_reg = visualizer_reg
        self._model_t = model_t
        self._ui_t_t = ui_t_t
        self._list_fn = list_fn

    def match_model(self, model_t, ui_t):
        if self._model_t is not None:
            return model_t is self._model_t
        if self._ui_t_t is not None:
            return isinstance(ui_t, self._ui_t_t)
        return True

    def call(self, ctx):
        if self._ui_t_t is not None:
            model_t = deduce_t(ctx.model)
            ui_t, system_fn_ref = self._visualizer_reg(model_t)
            fn_ctx = ctx.clone_with(
                piece=ui_t,
                system_fn_ref=system_fn_ref,
            )
        else:
            fn_ctx = ctx
        return self._system_fn.call(fn_ctx)

    def get_item_list(self, model):
        pass


class ViewFactoryReg:

    def __init__(self, visualizer_reg, config):
        self._visualizer_reg = visualizer_reg
        self._config = config

    def __getitem__(self, k):
        return self._config[k]

    def items(self, model=None):
        if model is None:
            model_t = None
            ui_t = None
        else:
            model_t = deduce_t(model)
            try:
                ui_t, unused_system_fn_ref = self._visualizer_reg(model_t)
            except KeyError:
                ui_t = None
        item_list = []
        for factory in self._config.values():
            if factory.match_model(model_t, ui_t):
                item_list += factory.get_item_list(model)
        return item_list


# d -> ViewFactory.
@mark.service
def view_factory_reg(config, visualizer_reg):
    return ViewFactoryReg(visualizer_reg, config)
