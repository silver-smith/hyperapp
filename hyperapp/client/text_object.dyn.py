import logging

from hyperapp.client.module import ClientModule
from hyperapp.client.object import Object
from . import htypes

_log = logging.getLogger(__name__)


class TextObject(Object):

    type = htypes.text.text_object_type(command_list=())

    @classmethod
    def from_state(cls, state):
        return cls(state.text)

    def __init__(self, text):
        self._text = text
        Object.__init__(self)

    @property
    def title(self):
        return 'Local text object'

    @property
    def data(self):
        return htypes.text.text(self._text)

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text
        self._notify_object_changed()

    def text_changed(self, new_text, emitter_view=None):
        self._text = new_text
        self._notify_object_changed(emitter_view)

    async def open_ref(self, ref_id):
        pass  # not implemented for local text

    # def __del__(self):
    #     _log.info('~text_object %r', self)


class WikiTextObject(TextObject):

    @classmethod
    def from_state(cls, state, async_ref_resolver):
        return cls(async_ref_resolver, state.text, state.ref_list)

    def __init__(self, async_ref_resolver, text, ref_list):
        super().__init__(text)
        self._async_ref_resolver = async_ref_resolver
        self._ref_list = ref_list

    @property
    def title(self):
        return 'wiki text'

    @property
    def data(self):
        return htypes.text.wiki_text(self._text, self._ref_list)

    async def open_ref(self, id):
        _log.info('Opening ref: %r', id)
        id2ref = {ref.id: ref.ref for ref in self._ref_list}
        ref = id2ref.get(int(id))
        if not ref:
            _log.warning('ref is missing: %r', id)
            return
        return (await self._async_ref_resolver.resolve_ref_to_piece(ref))


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.object_registry.register_actor(htypes.text.text, TextObject.from_state)
        services.object_registry.register_actor(htypes.text.wiki_text, WikiTextObject.from_state, services.async_ref_resolver)
