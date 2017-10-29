from .module import Module


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        services.href_object_registry.register('fs_ref', self.resolve_fs_object)

    def resolve_fs_object(self, fs_object):
        assert False, repr(fs_object)
