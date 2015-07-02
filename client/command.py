import weakref
from util import make_action


def make_cmd_action( cmd, widget, run, *args ):
    return make_action(widget, cmd.text, cmd.shortcut, run, cmd, *args)

def run_element_command( cmd, view, element_key ):
    view.run_object_element_command(cmd.id, element_key)

def make_element_action( cmd, widget, view, element_key ):
    def run( cmd, view_wr, element_key ):
        view = view_wr()
        if view:
            run_element_command(cmd, view, element_key)
    return make_cmd_action(cmd, widget, run, weakref.ref(view), element_key)
