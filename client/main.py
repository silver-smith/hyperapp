#!/usr/bin/env python

import sys
import os.path
import pickle
from PySide import QtCore, QtGui


sys.path.append('..')

from server import Server
from qt_keys import key_evt2str
from command import ModuleCommand
from view_command import command
import view
import window
import tab_view
import navigator
import list_view
#import narrower
import text_object
import text_edit
import object_selector
import article_ref
import ref_list


class Handle(view.Handle):

    def __init__( self, window_handles ):
        view.Handle.__init__(self)
        self.window_handles = window_handles

    def construct( self ):
        return Application(self.window_handles)


class Application(QtGui.QApplication, view.View):

    def __init__( self, server, server_commands, window_handles=None ):
        QtGui.QApplication.__init__(self, sys.argv)
        view.View.__init__(self)
        self.server = server
        self.server_commands = server_commands
        self._windows = []
        for handle in window_handles or []:
            self.open(handle)

    def handle( self ):
        return Handle([view.handle() for view in self._windows])

    def open( self, handle ):
        handle.construct(self)  # todo: remove window_created; use return value; refactor window duplication

    def pick_arg( self, kind ):
        return None

    def get_global_commands( self ):
        return self.server_commands + self._commands

    def window_created( self, view ):
        self._windows.append(view)

    def window_closed( self, view ):
        self._windows.remove(view)
    ##     if not self._windows:
    ##         module.save_state(Handle([view.handle()]))

    @command('Quit', 'Quit application', 'Alt+Q')
    def quit( self ):
        ## module.set_shutdown_flag()
        ## module.save_state(self.handle())
        QtGui.QApplication.quit()


def main():
    if len(sys.argv) > 1:
        path = dict(pair.split('=') for pair in sys.argv[1].split(','))  # module=file,fspath=/usr/portabe
    else:
        path=dict(
            module='file',
            fspath=os.path.expanduser('~'))

    server = Server(('localhost', 8888))

    get_request = dict(method='get', path=path)
    handle = server.get_handle(get_request)

    commands_request = dict(method='get_commands')
    commands_response = server.execute_request(commands_request)
    server_commands = [ModuleCommand.from_json(cmd) for cmd in commands_response['commands']]

    app = Application(server, server_commands)

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
                handle)]))
    win = handle.construct(app)
    app.exec_()

main()
