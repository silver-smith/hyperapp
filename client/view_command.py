import weakref
from util import make_action


class BoundViewCommand(object):

    def __init__( self, text, desc, shortcut, class_method, inst_wref ):
        self.text = text
        self.desc = desc
        self.shortcut = shortcut
        self.class_method = class_method
        self.inst_wref = inst_wref  # weak ref to class instance

    def get_inst( self ):
        return self.inst_wref()

    def run( self ):
        inst = self.inst_wref()
        if inst:  # inst not yet deleted?
            self.class_method(inst)

    def make_action( self, widget, window=None, app=None ):
        return make_action(widget, self.text, self.shortcut, self.run)


class UnboundViewCommand(object):

    def __init__( self, text, desc, shortcut, class_method ):
        self.text = text
        self.desc = desc
        self.shortcut = shortcut
        self.class_method = class_method

    def bind( self, inst ):
        return BoundViewCommand(self.text, self.desc, self.shortcut, self.class_method, weakref.ref(inst))


# decorator for view methods
class command(object):

    def __init__( self, text, desc, shortcut ):
        self.text = text
        self.desc = desc
        self.shortcut = shortcut

    def __call__( self, class_method ):
        return UnboundViewCommand(self.text, self.desc, self.shortcut, class_method)
