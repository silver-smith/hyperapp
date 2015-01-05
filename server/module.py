

class Module(object):

    module_registry = []

    def __init__( self ):
        self.module_registry.append(self)

    def init_phase2( self ):
        pass

    @classmethod
    def run_phase2_init( cls ):
        for module in cls.module_registry:
            module.init_phase2()

