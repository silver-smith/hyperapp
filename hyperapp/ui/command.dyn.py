import asyncio
import inspect
import logging
from functools import cached_property

from .services import (
    mark,
    pyobj_creg,
    ui_command_impl_creg,
    )

log = logging.getLogger(__name__)


_hardcoded_shortcuts = {
    'go_back': 'Esc',
    'go_forward': 'Alt+Right',
    'quit': 'Alt+Q',
    'open_model_commands': 'F1',
    'open': 'Return',
    'run_command': 'Return',
    'duplicate_tab': 'Shift+f4',
    'close_tab': 'Ctrl+f4',
    'duplicate_window': 'Alt+W',
    'open_layout_tree': 'Alt+L',
    'open_sample_static_text_1': 'F2',
    'open_sample_static_text_2': 'Ctrl+F2',
    'open_sample_static_list': 'f3',
    'open_sample_fn_list': 'f4',
    'open_sample_fn_tree': 'f6',
    'open_feed_sample_fn_list': 'f5',
    'open_feed_sample_fn_tree': 'Shift+f6',
    'open_sample_fn_record': 'F7',
    'show_state': 'Ctrl+Return',
    'details': 'Return',
    'open_view_item_commands': 'C',
    'add_view_command': 'Insert',
    'unwrap_master_details': 'Ctrl+U',
    'wrap_master_details': 'Ctrl+W',
    'move_tab_to_new_group': 'Shift+Alt+T',
    'open_tab_list': 'Alt+T',
    'browse_current_model': 'Ctrl+F1',
    'record_open': 'Return',
    'list_open': 'Return',
    'ref_list_open': 'Return',
    'open_file_bundle_list': 'Alt+B',
    'switch_list_to_tree': 'Alt+K',
    'open_opener_commands': 'Alt+O',
    'toggle_open_command': 'Space',
    'open_local_server_context': 'Alt+S',
    'show_current_context': 'Alt+U',
    }


def d_to_name(d):
    name = d._t.name
    assert name.endswith('_d'), repr(name)
    return name[:-2]


def d_res_ref_to_name(d_ref):
    d = pyobj_creg.invite(d_ref)
    return d_to_name(d)


class Command:

    def __init__(self, d, impl):
        self._d = d
        self._impl = impl

    @property
    def d(self):
        return self._d

    @cached_property
    def name(self):
        return d_to_name(self._d)

    @property
    def enabled(self):
        return self._impl.enabled

    @property
    def disabled_reason(self):
        return self._impl.disabled_reason

    @property
    def shortcut(self):
        return _hardcoded_shortcuts.get(self.name)

    def start(self):
        log.info("Start command: %r", self.name)
        asyncio.create_task(self.run())

    async def run(self):
        return await self._impl.run()


class CommandImpl:

    async def run(self):
        if not self.enabled:
            raise RuntimeError(f"{self!r}: Disabled: {self.disabled_reason}")
        result = await self._run()
        if type(result) is list:
            result = tuple(result)
        return result


class FnCommandImpl(CommandImpl):

    def __init__(self, ctx, fn, params):
        super().__init__()
        self._ctx = ctx
        self._fn = fn
        self._params = set(params)

    def __repr__(self):
        return f"{self.__class__.__name__} #{hex(id(self))[-6:]}: {self._fn.__name__}"

    @property
    def name(self):
        return self._fn.__name__

    @property
    def enabled(self):
        return set(self.params) >= self._params

    @property
    def disabled_reason(self):
        params = ", ".join(self._params - set(self.params))
        return f"Params not ready: {params}"

    async def _run(self):
        params = self.params
        kw = {
            name: value
            for name, value
            in params.items()
            if name in self._params
            }
        log.info("Run command: %r (%s)", self, kw)
        result = self._fn(**kw)
        if inspect.iscoroutinefunction(self._fn):
            result = await result
        log.info("Run command %r result: [%s] %r", self, type(result), result)
        return result

    @property
    def params(self):
        params = {
            **self._ctx.as_dict(),
            'ctx': self._ctx,
            }
        try:
            view = self._ctx.view
        except KeyError:
            return params
        try:
            widget = self._ctx.widget()
        except KeyError:
            return params
        if widget is None:
            raise RuntimeError(f"{self!r}: widget is gone")
        params['widget'] = widget
        params['state'] = view.widget_state(widget)
        return params
