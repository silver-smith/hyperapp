import logging
import weakref

from hyperapp.common.htypes.deduce_value_type import deduce_value_type

from . import htypes
from .services import (
    association_reg,
    data_to_res,
    mark,
    pyobj_creg,
    )

log = logging.getLogger(__name__)


class UiCommand:

    def __init__(self, name, fn, piece, view, widget, wrappers):
        self._name = name
        self._fn = fn
        self._piece = piece
        self._view = view
        self._widget = weakref.ref(widget)
        self._wrappers = wrappers

    @property
    def name(self):
        return self._name

    async def run(self):
        widget = self._widget()
        if widget is None:
            log.warning("Not running UI command %r: Widget is gone", self._name)
            return None
        state = self._view.widget_state(self._piece, widget)
        log.info("Run ui command: %r (%s, %s)", self._name, self._piece, state)
        result = self._fn(self._piece, state)
        log.info("Run ui command %r result: [%s] %r", self._name, type(result), result)
        if result is None:
            return None
        for wrapper in reversed(self._wrappers):
            result = wrapper(result)
        log.info("Run ui command %r wrapped result: [%s] %r", self._name, type(result), result)
        return result


@mark.service
def ui_command_factory():
    def _ui_command_factory(view_piece, view, widget, wrappers):
        piece_t = deduce_value_type(view_piece)
        piece_t_res = pyobj_creg.reverse_resolve(piece_t)
        d_res = data_to_res(htypes.ui.ui_command_d())
        command_list = []
        for fn_res in association_reg.get_all((d_res, piece_t_res)):
            fn = pyobj_creg.animate(fn_res)
            command_list.append(UiCommand(fn.__name__, fn, view_piece, view, widget, wrappers))
        return command_list
    return _ui_command_factory
