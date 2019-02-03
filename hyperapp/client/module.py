from ..common.module import Module
from .commander import Commander


class ClientModule(Module, Commander):

    def __init__(self, name, services):
        Module.__init__(self, name)
        Commander.__init__(self, commands_kind='global')
