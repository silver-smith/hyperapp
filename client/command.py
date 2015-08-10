import weakref
from common.interface import tCommand
from util import make_action


Command = tCommand.instantiate


def make_cmd_action( cmd, widget, run, *args ):
    return make_action(widget, cmd.text, cmd.shortcut, run, cmd, *args)

def run_object_command( cmd, view ):
    view.run_object_command(cmd.id)

def make_object_cmd_action( cmd, widget, view ):
    def run( cmd, view_wr ):
        view = view_wr()
        if view:
            run_object_command(cmd, view)
    return make_cmd_action(cmd, widget, run, weakref.ref(view))

def run_element_command( cmd, view, element_key ):
    view.run_object_element_command(cmd.id, element_key)

def make_element_cmd_action( cmd, widget, view, element_key ):
    def run( cmd, view_wr, element_key ):
        view = view_wr()
        if view:
            run_element_command(cmd, view, element_key)
    return make_cmd_action(cmd, widget, run, weakref.ref(view), element_key)
