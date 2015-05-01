import weakref
from util import is_list_inst, make_action


class BoundViewCommand(object):

    def __init__( self, text, desc, shortcut, enabled, class_method, inst_wref ):
        self.text = text
        self.desc = desc
        self.shortcut = shortcut
        self.class_method = class_method
        self.inst_wref = inst_wref  # weak ref to class instance
        self.enabled = enabled

    def is_enabled( self ):
        return self.enabled

    # returns basestring list
    def get_shortcut_list( self ):
        if isinstance(self.shortcut, basestring):
            return [self.shortcut]
        else:
            return self.shortcut or []

    def get_inst( self ):
        return self.inst_wref()

    def run( self ):
        inst = self.inst_wref()
        if inst:  # inst not yet deleted?
            self.class_method(inst)

    # must take same parameters as window.OpenCommand as they are both used as interchangeable by menu bar global menu
    def make_action( self, widget, window=None ):
        action = make_action(widget, self.text, self.shortcut, self.run)
        action.setEnabled(self.enabled)
        return action

    def clone_without_shortcuts( self, shortcut_set ):
        new_shortcuts = set(self.get_shortcut_list()) - shortcut_set
        return BoundViewCommand(self.text, self.desc, list(new_shortcuts), self.enabled, self.class_method, self.inst_wref)

    def setEnabled( self, enabled ):
        if enabled != self.enabled:
            self.enabled = enabled
            inst = self.inst_wref()
            if inst:
                inst.view_changed()

    def enable( self ):
        self.setEnabled(True)

    def disable( self ):
        self.setEnabled(False)


class UnboundViewCommand(object):

    def __init__( self, text, desc, shortcut, enabled, class_method ):
        self.text = text
        self.desc = desc
        self.shortcut = shortcut
        self.enabled = enabled
        self.class_method = class_method

    def bind( self, inst ):
        bound_cmd = BoundViewCommand(self.text, self.desc, self.shortcut, self.enabled, self.class_method, weakref.ref(inst))
        self.setEnabled = bound_cmd.setEnabled
        self.enable = bound_cmd.enable
        self.disable = bound_cmd.disable
        return bound_cmd


# decorator for view methods
class command(object):

    def __init__( self, text, desc, shortcut, enabled=True ):
        assert shortcut is None or isinstance(shortcut, basestring) or is_list_inst(shortcut, basestring), repr(shortcut)
        self.text = text
        self.desc = desc
        self.shortcut = shortcut  # basestring for single shortcut, basestring list for multiple
        self.enabled = enabled

    def __call__( self, class_method ):
        return UnboundViewCommand(self.text, self.desc, self.shortcut, self.enabled, class_method)
