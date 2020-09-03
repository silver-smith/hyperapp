import logging
from collections import namedtuple

from hyperapp.client.module import ClientModule

_log = logging.getLogger(__name__)


_ResolvedPiece = namedtuple('_ResolvedPiece', 'object layout_handle')


class LayoutCommand:

    def __init__(self, id, code_command, layout_ref=None, args=None, kw=None, layout_handle=None, wrapper=None):
        self.id = id
        self.code_command = code_command
        self.layout_ref = layout_ref
        self._args = args or ()
        self._kw = kw or {}
        self._layout_handle = layout_handle
        self._wrapper = wrapper
        self.kind = code_command.kind
        self.resource_key = code_command.resource_key  # todo: use id

    def __repr__(self):
        return (
            f"LayoutCommand("
            f" id={self.id}"
            f" code_command={self.code_command}"
            f" layout_ref={self.layout_ref})"
            f" args={self._args}"
            f" kw={self._kw}"
            f" wrapper={self._wrapper}"
            f")"
            )

    def with_(self, **kw):
        old_kw = dict(
            args=self._args,
            kw=self._kw,
            layout_handle=self._layout_handle,
            wrapper=self._wrapper,
            )
        all_kw = {**old_kw, **kw}
        return LayoutCommand(self.id, self.code_command, self.layout_ref, **all_kw)

    def partial(self, *args, **kw):
        return self.with_(args=args, kw=kw)

    def is_enabled(self):
        return True  # todo

    async def run(self, *args, **kw):
        full_args = (*self._args, *args)
        full_kw = {**self._kw, **kw}
        _log.info("LayoutCommand: run: (%r) args=%r kw=%r", self, full_args, full_kw)
        result = await self.code_command.run(*full_args, **full_kw)
        return (await self._wrap_result(result))

    async def _wrap_result(self, result):
        if result is None:
            return
        piece = result
        object = await this_module.object_registry.resolve_async(piece)
        if self.layout_ref:
            layout_handle = await self._layout_handle.command_handle(self.id, self.layout_ref)
        else:
            layout_handle = await this_module.layout_handle_from_object_type(object.type)
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
        self.layout_handle_from_object_type = services.layout_handle_from_object_type
