from .services import (
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.view_factory import ViewFactory


class ViewFactoryTemplate:

    @classmethod
    @mark.actor.cfg_item_creg
    def from_piece(cls, piece):
        return cls(
            k=web.summon(piece.k),
            ui_t_t=pyobj_creg.invite_opt(piece.ui_t_t),
            view_t=pyobj_creg.invite(piece.view_t),
            is_wrapper=piece.is_wrapper,
            view_ctx_params=piece.view_ctx_params,
            system_fn=web.summon(piece.system_fn),
            )

    def __init__(self, k, ui_t_t, view_t, is_wrapper, view_ctx_params, system_fn):
        self._k = k
        self._ui_t_t = ui_t_t
        self._view_t = view_t
        self._is_wrapper = is_wrapper
        self._view_ctx_params = view_ctx_params
        self._system_fn = system_fn

    @property
    def key(self):
        return self._k

    def resolve(self, system, service_name):
        system_fn_creg = system.resolve_service('system_fn_creg')
        return ViewFactory(
            k=self._k,
            ui_t_t=self._ui_t_t,
            view_t=self._view_t,
            is_wrapper=self._is_wrapper,
            view_ctx_params=self._view_ctx_params,
            system_fn=system_fn_creg.animate(self._system_fn),
            )
