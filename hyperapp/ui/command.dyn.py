import asyncio
import inspect
import logging
from functools import cached_property
from enum import Enum

from .services import (
    pyobj_creg,
    )

log = logging.getLogger(__name__)


class CommandKind(Enum):
    VIEW = 'view'
    MODEL = 'model'


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
    'toggle_editable': 'Ctrl+E',
    'open_command_layout_context': 'L',
    'add_identity_command': 'I',
    'rename_command': 'R',
    'set_command_name': 'Return',
    }


def d_to_name(d):
    name = d._t.name
    assert name.endswith('_d'), repr(name)
    return name[:-2]


def d_res_ref_to_name(d_ref):
    d = pyobj_creg.invite(d_ref)
    return d_to_name(d)


class UnboundCommandBase:

    def __init__(self, d):
        self._d = d

    @property
    def d(self):
        return self._d

    @cached_property
    def name(self):
        return d_to_name(self._d)


class UnboundCommand(UnboundCommandBase):

    def __init__(self, d, ctx_fn):
        super().__init__(d)
        self._ctx_fn = ctx_fn

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name}: {self._ctx_fn}>"


class BoundCommandBase:

    def __init__(self, d):
        self._d = d

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"

    @property
    def d(self):
        return self._d

    @cached_property
    def name(self):
        return d_to_name(self._d)

    @property
    def shortcut(self):
        return _hardcoded_shortcuts.get(self.name)

    def start(self):
        log.info("Start command: %r", self.name)
        asyncio.create_task(self.run())


class BoundCommand(BoundCommandBase):

    def __init__(self, d, ctx_fn, ctx):
        super().__init__(d)
        self._ctx_fn = ctx_fn
        self._ctx = ctx

    @property
    def enabled(self):
        return not self._missing_params

    @property
    def disabled_reason(self):
        params = ", ".join(self._missing_params)
        return f"Params not ready: {params}"

    async def run(self):
        if not self.enabled:
            raise RuntimeError(f"{self!r}: Disabled: {self.disabled_reason}")
        result = await self._run()
        if type(result) is list:
            result = tuple(result)
        return result

    async def _run(self):
        # log.info("Run command: %r (%s)", self, kw)
        result = self._ctx_fn.call(self._ctx)
        if inspect.iscoroutine(result):
            result = await result
        log.info("Run command %r result: [%s] %r", self, type(result), result)
        return result

    @cached_property
    def _missing_params(self):
        return self._ctx_fn.missing_params(self._ctx)
