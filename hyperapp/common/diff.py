import abc


class Diff(object, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def to_data(self, iface):
        pass


class SimpleDiff(Diff):

    def __init__(self, value):
        Diff.__init__(self)
        self.value = value

    def to_data(self, iface):
        return self.value
