import abc
import weakref


class ChooserCallback(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    async def element_chosen(self, key):
        pass


class Chooser:

    def __init__(self):
        self._chooser_callback = None

    def chooser_set_callback(self, callback: ChooserCallback):
        self._chooser_callback = callback

    async def chooser_call_callback(self, key):
        return (await self._chooser_callback.element_chosen(key))
