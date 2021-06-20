from .module import ClientModule


class LCSheet:

    def __init__(self):
        self._dir_to_piece = {}

    def register(self, dir_list, piece):
        for dir in dir_list:
            self._dir_to_piece[tuple(dir)] = piece

    def resolve(self, dir_list):
        for dir in reversed(dir_list):
            try:
                return self._dir_to_piece[tuple(dir)]
            except KeyError:
                pass
        raise RuntimeError(f"No dir among {dir_list} is registered at LCS")


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.lcs = LCSheet()
