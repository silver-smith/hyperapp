import asyncio
import weakref
import traceback
from .util import WeakSetWithCallback
from .command import Commandable


class ObjectObserver(object):

    def object_changed( self ):
        pass


class Object(Commandable):

    def __init__( self ):
        Commandable.__init__(self)
        self._init_observers()

    def get_title( self ):
        raise NotImplementedError(self.__class__)

    def to_data( self ):
        raise NotImplementedError(self.__class__)

    def get_url( self ):
        return None

    def get_facets( self ):
        return []

    def get_module_ids( self ):
        return []

    @asyncio.coroutine
    def run_command( self, command_id, *args, **kw ):
        for command in self._commands:
            if command.id == command_id:
                break
        else:
            assert False, repr(command_id)  # Unknown command
        return (yield from command.run(*args, **kw))

    def subscribe( self, observer ):
        assert isinstance(observer, ObjectObserver), repr(observer)
        self._observers.add(observer)

    def unsubscribe( self, observer ):
        self._observers.remove(observer)

    @asyncio.coroutine
    def server_subscribe( self ):
        pass

    def observers_gone( self ):
        pass

    def _init_observers( self ):
        def on_remove( self_ref=weakref.ref(self) ):
            self = self_ref()
            if self:
                self._on_subscriber_removed()
        self._observers = WeakSetWithCallback(on_remove=on_remove)

    def _on_subscriber_removed( self ):
        try:
            if not self._observers:  # this was last reference to me
                self.observers_gone()
        except:
            traceback.print_exc()

    def _notify_object_changed( self, skip_observer=None ):
        for observer in self._observers:
            if observer is not skip_observer:
                observer.object_changed()
