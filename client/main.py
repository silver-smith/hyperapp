#!/usr/bin/env python

import sys
import os.path
import pickle
from PySide import QtCore, QtGui


sys.path.append('..')

import json_connection
from list_obj import ListObj

from qt_keys import key_evt2str
from util import DEBUG_FOCUS, DEBUG_EVENTS
from command import command_owner_meta_class, command
import view
import window
import tab_view
import navigator
import list_view
#import narrower


class Handle(view.Handle):

    def __init__( self, window_handles ):
        view.Handle.__init__(self)
        self.window_handles = window_handles

    def construct( self ):
        return Application(self.window_handles)


class Application(QtGui.QApplication, view.View):

    __metaclass__ = command_owner_meta_class

    def __init__( self, window_handles=None ):
        QtGui.QApplication.__init__(self, sys.argv)
        view.View.__init__(self)
        if DEBUG_FOCUS:
            self.focusChanged.connect(self._on_focus_changed)
        if DEBUG_EVENTS:
            self.installEventFilter(self)
        self._windows = []
        for handle in window_handles or []:
            self.open(handle)

    def handle( self ):
        return Handle([view.handle() for view in self._windows])

    def open( self, handle ):
        handle.construct(self)  # todo: remove window_created; use return value; refactor window duplication

    def pick_arg( self, kind ):
        return None

    def get_arg_editor( self, kind, args ):
        return kind.get_handle(args)

    def global_commands( self ):
        return []
    ##     return Module.get_global_commands() + [self.quit]

    def window_created( self, view ):
        self._windows.append(view)

    def window_closed( self, view ):
        self._windows.remove(view)
    ##     if not self._windows:
    ##         module.save_state(Handle([view.handle()]))

    @command('Alt+Q', 'Quit application')
    def quit( self ):
        ## module.set_shutdown_flag()
        ## module.save_state(self.handle())
        QtGui.QApplication.quit()


def main():
    app = Application()

    connection = json_connection.ClientConnection(('localhost', 8888))
    request = dict(method='init')
    connection.send(request)
    response = connection.receive()
    obj = ListObj(connection, response)

    #obj = fsopen('/tmp')
    #obj = process.Process('/usr', 'find')
    #obj = process.Process('/usr/portage', 'ls -l')
    #obj = process.Process('/usr/portage', 'i=0; while [ $i -lt 50 ]; do sleep 1; echo -n "-$i-"; i=$(($i+1)); if [ $(($i%10)) -eq 0 ]; then echo; fi; done')
    #obj = process.Process('/usr/portage', 'nohup /bin/bash -e "i=0; while [ $i -lt 10000 ]; do sleep 0.01; echo -n "-$i-"; i=$(($i+1)); if [ $(($i%10)) -eq 0 ]; then echo; fi; done"')
    #obj = process.ProcessList(process.module)
    #obj = file_view.File(os.path.expanduser('~/tmp/numbered.txt'))
    #obj = file_view.File('list_view.py')
    handle = window.Handle(
        tab_view.Handle([
            navigator.Handle(
                list_view.Handle(obj))]))
    win = handle.construct(app)
    app.exec_()

main()
