import weakref


class ObjectObserver(object):

    def object_changed( self ):
        pass


class Object(object):

    def __init__( self ):
        self._init_observers()

    def _init_observers( self ):
        self._observers = weakref.WeakSet()

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

    def run_command( self, command_id ):
        raise NotImplementedError(self.__class__)

    def subscribe( self, observer ):
        assert isinstance(observer, ObjectObserver), repr(observer)
        self._observers.add(observer)

    def _notify_object_changed( self, skip_observer ):
        for observer in self._observers:
            if observer is not skip_observer:
                observer.object_changed()
