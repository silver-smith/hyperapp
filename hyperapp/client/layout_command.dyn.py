import logging
from collections import namedtuple

from hyperapp.client.module import ClientModule

_log = logging.getLogger(__name__)


_ResolvedPiece = namedtuple('_ResolvedPiece', 'object layout_handle')


class LayoutCommand:

    def __init__(self, id, code_command, path, layout_ref=None, args=None, kw=None, wrapper=None):
        self.id = id
        self.code_command = code_command
        self.path = path
        self.layout_ref = layout_ref
        self._args = args or ()
        self._kw = kw or {}
        self._wrapper = wrapper
        self.kind = code_command.kind
        self.resource_key = code_command.resource_key  # todo: use id

    def __repr__(self):
        return (f"LayoutCommand(id={self.id} code_command={self.code_command} path={self.path} layout_ref={self.layout_ref})"
                f" args={self._args} kw={self._kw} wrapper={self._wrapper})")

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
        return (await self._wrap_result(object, result))

    async def _wrap_result(self, origin_object, result):
        if result is None:
            return
        piece = result
        object = await this_module.object_registry.resolve_async(piece)
        if self.layout_ref:
            assert 0  # todo
        layout_handle = await this_module.layout_handle_registry.produce_handle(object)
        resolved_piece = _ResolvedPiece(object, layout_handle)
        _log.info("LayoutCommand: piece resolved to: %r", resolved_piece)
        if not self._wrapper:
            return resolved_piece
        _log.info("LayoutCommand: wrap resolved piece with: %r", self._wrapper)
        await self._wrapper(resolved_piece)


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        self.object_registry = services.object_registry
        self.layout_handle_registry = services.layout_handle_registry
