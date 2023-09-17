import logging
import weakref

from hyperapp.common.htypes.deduce_value_type import deduce_value_type

from . import htypes
from .services import (
    association_reg,
    data_to_res,
    pyobj_creg,
    mark,
    )

log = logging.getLogger(__name__)


class UnboundUiCommand:

    def __init__(self, name, layout, ctl, fn):
        self._name = name
        self._layout = layout
        self._ctl = ctl
        self._fn = fn

    def bind(self, widget):
        return BoundUiCommand(self._name, self._layout, self._ctl, self._fn, widget)


class BoundUiCommand:

    def __init__(self, name, layout, ctl, fn, widget):
        self._name = name
        self._layout = layout
        self._ctl = ctl
        self._fn = fn
        self._widget = weakref.ref(widget)

    @property
    def name(self):
        return self._name

    def run(self, **kw):
        widget = self._widget()
        if widget is None:
            log.warning("Not running UI command %r: Widget is gone", self._name)
            return None
        state = self._ctl.widget_state(widget)
        return self._fn(self._layout, state, **kw)


@mark.service
def ui_command_factory():
    def _ui_command_factory(layout, ctl):
        layout_t = deduce_value_type(layout)
        layout_t_res = pyobj_creg.reverse_resolve(layout_t)
        d_res = data_to_res(htypes.ui.ui_command_d())
        command_list = []
        for fn_res in association_reg.get_all((d_res, layout_t_res)):
            fn = pyobj_creg.animate(fn_res)
            command_list.append(UnboundUiCommand(fn.__name__, layout, ctl, fn))
        return command_list
    return _ui_command_factory
