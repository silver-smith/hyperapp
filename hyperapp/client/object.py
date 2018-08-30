import logging
import weakref
import traceback
from collections import namedtuple

from .weak_key_dictionary_with_callback import WeakKeyDictionaryWithCallback
from .command_class import Commander

log = logging.getLogger(__name__)


class ObjectObserver(object):

    def object_changed(self, *args, **kw):
        pass


class Object(Commander):

    ObserverArgs = namedtuple('ObserverArgs', 'args kw')

    def __init__(self):
        Commander.__init__(self, commands_kind='object')
        self._init_observers()

    def get_title(self):
        raise NotImplementedError(self.__class__)

    def to_data(self):
        raise NotImplementedError(self.__class__)

    # collect references for currently visible objects
    def pick_current_refs(self):
        return []

    def get_url(self):
        return None

    def get_facets(self):
        return []

    async def run_command(self, command_id, *args, **kw):
        command = self.get_command(command_id)
        assert command, 'Unknown command: %r; known are: %r' % (command_id, [cmd.id for cmd in self._commands])  # Unknown command
        return (await command.run(*args, **kw))

    def subscribe(self, observer, *args, **kw):
        assert isinstance(observer, ObjectObserver), repr(observer)
        log.debug('-- Object.subscribe self=%s/%s, observer=%s/%s', id(self), self, id(observer), observer)
        self._observers[observer] = self.ObserverArgs(args, kw)

    def unsubscribe(self, observer):
        log.debug('-- Object.unsubscribe; self=%s/%r, observer=%s/%s', id(self), self, id(observer), observer)
        del self._observers[observer]
        self._on_subscriber_removed()

    def observers_gone(self):
        pass

    def _init_observers(self):
        def on_remove(self_ref=weakref.ref(self)):
            self = self_ref()
            if self:
                log.debug('-- Object: observer is gone; self=%s/%r', id(self), self)
                self._on_subscriber_removed()
        self._observers = WeakKeyDictionaryWithCallback(on_remove=on_remove)

    def _on_subscriber_removed(self):
        try:
            if not self._observers:  # this was last reference to me
                log.debug('-- Object.observers_gone self=%s/%r', id(self), self)
                self.observers_gone()
        except:
            traceback.print_exc()

    def _notify_object_changed(self, skip_observer=None):
        log.debug('-- Object._notify_object_changed, self=%s/%s observers count=%s', id(self), self, len(self._observers))
        for observer, rec in self._observers.items():
            log.debug('-- Object._notify_object_changed, observer=%s (*%s, **%s), skip=%r',
                          id(observer), rec.args, rec.kw, observer is skip_observer)
            if observer is not skip_observer:
                observer.object_changed(*rec.args, **rec.kw)
