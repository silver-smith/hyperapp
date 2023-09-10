from hyperapp.common.htypes.deduce_value_type import deduce_value_type

from . import htypes
from .services import (
    association_reg,
    pyobj_creg,
    mark,
    )


class UiCommand:

    def __init__(self, name, fn):
        self._name = name
        self._fn = fn

    def run(self, **kw):
        return self._fn(**kw)


@mark.service
def ui_command_factory():
    def _ui_command_factory(layout):
        layout_t = deduce_value_type(layout)
        fn_res = association_reg[htypes.ui.ui_command_d(), layout_t]
        fn = pyobj_creg.animate(fn_res)
        return [UiCommand(layout_t.name, fn)]
    return _ui_command_factory
