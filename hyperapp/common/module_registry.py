import abc


class ModuleRegistry(object, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def register(self, module):
        pass
