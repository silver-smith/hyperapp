import logging

_log = logging.getLogger(__name__)


class LayoutCommand:

    def __init__(self, id, code_command, path, layout_ref, args=None, kw=None, wrapper=None):
        self.id = id
        self.code_command = code_command
        self.path = path
        self.layout_ref = layout_ref
        self._args = args or ()
        self._kw = kw or {}
        self._wrapper = wrapper
        self.kind = code_command.kind
        self.resource_key = code_command.resource_key  # todo

    def __repr__(self):
        return f"LayoutCommand(id={self.id} code_command={self.code_command} path={self.path} layout_ref={self.layout_ref})"

    def with_(self, **kw):
        old_kw = dict(
            args=self._args,
            kw=self._kw,
            wrapper=self._wrapper,
            )
        all_kw = {**old_kw, **kw}
        return LayoutCommand(self.id, self.code_command, self.path, self.layout_ref, **all_kw)

    def partial(self, *args, **kw):
        return self.with_(args=args, kw=kw)

    def is_enabled(self):
        return True  # todo

    async def run(self, *args, **kw):
        full_args = (*self._args, *args)
        full_kw = {**self._kw, **kw}
        _log.info("LayoutCommand: run: (%r) args=%r kw=%r", self, full_args, full_kw)
        result = await self.code_command.run(*full_args, **full_kw)
        if not self._wrapper:
            return result
        _log.info("LayoutCommand: wrap result with: %r", self._wrapper)
        await self._wrapper(result)
