from .services import (
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.view_factory import ViewFactory, ViewMultiFactory


class ViewFactoryTemplate:

    @classmethod
    @mark.actor.cfg_item_creg
    def from_piece(cls, piece):
        return cls(
            k=web.summon(piece.k),
            model_t=pyobj_creg.invite_opt(piece.model_t),
            ui_t_t=pyobj_creg.invite_opt(piece.ui_t_t),
            view_t=pyobj_creg.invite(piece.view_t),
            is_wrapper=piece.is_wrapper,
            view_ctx_params=piece.view_ctx_params,
            system_fn=web.summon(piece.system_fn),
            )

    def __init__(self, k, model_t, ui_t_t, view_t, is_wrapper, view_ctx_params, system_fn):
        assert not (model_t is not None and ui_t_t is not None)  # Not both.
        self._k = k
        self._model_t = model_t
        self._ui_t_t = ui_t_t
        self._view_t = view_t
        self._is_wrapper = is_wrapper
        self._view_ctx_params = view_ctx_params
        self._system_fn = system_fn

    @property
    def key(self):
        return self._k

    def resolve(self, system, service_name):
        system_fn_creg = system['system_fn_creg']
        return ViewFactory(
            visualizer_reg=system['visualizer_reg'],
            k=self._k,
            model_t=self._model_t,
            ui_t_t=self._ui_t_t,
            view_t=self._view_t,
            is_wrapper=self._is_wrapper,
            view_ctx_params=self._view_ctx_params,
            system_fn=system_fn_creg.animate(self._system_fn),
            )


class ViewFactoryMultiTemplate:

    @classmethod
    @mark.actor.cfg_item_creg
    def from_piece(cls, piece):
        return cls(
            k=web.summon(piece.k),
            model_t=pyobj_creg.invite_opt(piece.model_t),
            ui_t_t=pyobj_creg.invite_opt(piece.ui_t_t),
            list_fn=web.summon(piece.list_fn),
            )

    def __init__(self, k, model_t, ui_t_t, list_fn):
        assert not (model_t is not None and ui_t_t is not None)  # Not both.
        self._k = k
        self._model_t = model_t
        self._ui_t_t = ui_t_t
        self._list_fn = list_fn

    @property
    def key(self):
        return self._k

    def resolve(self, system, service_name):
        system_fn_creg = system['system_fn_creg']
        return ViewMultiFactory(
            visualizer_reg=system['visualizer_reg'],
            model_t=self._model_t,
            ui_t_t=self._ui_t_t,
            list_fn=system_fn_creg.animate(self._list_fn),
            )
