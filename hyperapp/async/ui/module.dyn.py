from hyperapp.common.module import Module

from .commander import Commander


class ClientModule(Module, Commander):

    category_list = ['global']

    def __init__(self, name, services, config):
        Module.__init__(self, name)
        Commander.__init__(self, commands_kind='global')
