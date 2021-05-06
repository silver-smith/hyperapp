import logging

from . import htypes
from .object import Object
from .module import ClientModule

_log = logging.getLogger(__name__)


class WikiTextObject(Object):

    @classmethod
    def from_state(cls, state, async_web):
        return cls(async_web, state.text, state.ref_list)

    def __init__(self, async_web, text, ref_list):
        super().__init__()
        self._text = text
        self._async_web = async_web
        self._ref_list = ref_list

    @property
    def title(self):
        return 'Wiki text'

    @property
    def piece(self):
        return htypes.text.wiki_text(self._text, self._ref_list)

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

    async def open_ref(self, id):
        _log.info('Opening ref: %r', id)
        id2ref = {ref.id: ref.ref for ref in self._ref_list}
        ref = id2ref.get(int(id))
        if not ref:
            _log.warning('ref is missing: %r', id)
            return
        return (await self._async_web.summon(ref))


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services)
        services.object_registry.register_actor(htypes.text.wiki_text, WikiTextObject.from_state, services.async_web)
