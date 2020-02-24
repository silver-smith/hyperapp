import abc
import weakref


class ChooserObserver(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def element_chosen(self, key):
        pass


class ChooserSubject:

    def __init__(self):
        self._chooser_observer_set = weakref.WeakSet()

    def chooser_subscribe(self, observer: ChooserObserver):
        self._chooser_observer_set.add(observer)

    def chooser_unsubscribe(self, observer: ChooserObserver):
        self._chooser_observer_set.remove(observer)
