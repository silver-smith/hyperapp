import asyncio
import inspect
import logging
from functools import cached_property
from enum import Enum

from .code.directory import d_to_name

log = logging.getLogger(__name__)


class CommandKind(Enum):
    VIEW = 'view'
    MODEL = 'model'


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

    @property
    def fn(self):
        return self._ctx_fn

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name}: {self._ctx_fn}>"


class BoundCommandBase:

    def __init__(self, d, ctx):
        self._d = d
        self._ctx = ctx

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"

    @property
    def d(self):
        return self._d

    @cached_property
    def name(self):
        return d_to_name(self._d)

    def update_ctx(self, **kw):
        self._ctx.update(**kw)

    def start(self):
        log.info("Start command: %r", self.name)
        asyncio.create_task(self.run())


class BoundCommand(BoundCommandBase):

    def __init__(self, d, ctx_fn, ctx):
        super().__init__(d, ctx)
        self._ctx_fn = ctx_fn

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
        return await self._run()

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


def _amend_fragment(text):
    if text.endswith('...'):
        suffix = '...'
        text = text.removesuffix('...')
    else:
        suffix = ''
    text = text.split('.')[-1]
    text = text.removesuffix('()')
    text = text.removesuffix('_d')
    text = text.replace('_', ' ')
    text = text.capitalize()
    return text + suffix


def command_d_text(format, d):
    text = format(d)
    fragments = text.split(': ')
    amended_fragments = [_amend_fragment(f) for f in fragments]
    return ": ".join(amended_fragments)


def command_text(format, command):
    return command_d_text(format, command.d)
