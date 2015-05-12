import weakref
from util import WeakSetWithCallback


class ObjectObserver(object):

    def object_changed( self ):
        pass


class Object(object):

    def __init__( self ):
        self._init_observers()

    def __getstate__( self ):
        state = dict(self.__dict__)
        del state['_observers']
        return state

    def __setstate__( self, state ):
        self.__dict__.update(state)
        self._init_observers()

    def get_title( self ):
        raise NotImplementedError(self.__class__)

    def get_commands( self ):
        raise NotImplementedError(self.__class__)

    def run_command( self, initiator_view, command_id ):
        raise NotImplementedError(self.__class__)

    def subscribe( self, observer ):
        assert isinstance(observer, ObjectObserver), repr(observer)
        self._observers.add(observer)

    def observers_gone( self ):
        pass

    def _init_observers( self ):
        def on_remove( self_ref=weakref.ref(self) ):
            self = self_ref()
            if self:
                self._on_subscriber_removed()
        self._observers = WeakSetWithCallback(on_remove=on_remove)

    def _on_subscriber_removed( self ):
        if not self._observers:  # this was last reference to me
            self.observers_gone()

    def _notify_object_changed( self, skip_observer=None ):
        for observer in self._observers:
            if observer is not skip_observer:
                observer.object_changed()
