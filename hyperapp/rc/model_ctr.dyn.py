from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.rc_constructor import ModuleCtr


class ModelCtr(ModuleCtr):

    @classmethod
    def from_piece(cls, piece):
        return cls(
            module_name=piece.module_name,
            attr_qual_name=piece.attr_qual_name,
            model_t=pyobj_creg.invite(piece.model_t),
            ui_t=web.summon(piece.ui_t),
            ctx_params=piece.ctx_params,
            service_params=piece.service_params,
            )

    def __init__(self, module_name, attr_qual_name, model_t, ui_t, ctx_params, service_params):
        super().__init__(module_name)
        self._attr_qual_name = attr_qual_name
        self._model_t = model_t
        self._ui_t = ui_t
        self._ctx_params = ctx_params
        self._service_params = service_params

    @property
    def piece(self):
        return htypes.model_resource.model_ctr(
            module_name=self._module_name,
            attr_qual_name=tuple(self._attr_qual_name),
            model_t=pyobj_creg.actor_to_ref(self._model_t),
            ui_t=mosaic.put(self._ui_t),
            ctx_params=tuple(self._ctx_params),
            service_params=tuple(self._service_params),
            )

    def update_resource_targets(self, resource_tgt, target_set):
        assert 0, f'todo: {resource_tgt.name} / {self._module_name} : {self._model_t} - {self._ui_t}'
        pass
