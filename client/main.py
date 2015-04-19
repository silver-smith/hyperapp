#!/usr/bin/env python

import sys
import os.path
from PySide import QtCore, QtGui


sys.path.append('..')

from util import pickle_dumps, pickle_loads
from server import Server
from qt_keys import key_evt2str
from command import ModuleCommand
from view_command import command
import view
import window
import tab_view
import navigator
import list_view
import narrower
import text_object
import proxy_text_object
import text_edit
import text_view
import object_selector
import ref_list
import proxy_registry


STATE_FILE_PATH = os.path.expanduser('~/.hyperapp.state')


class Application(QtGui.QApplication, view.View):

    def __init__( self, server_commands, window_handles=None ):
        QtGui.QApplication.__init__(self, sys.argv)
        view.View.__init__(self)
        self.server_commands = server_commands
        self._windows = []
        for handle in window_handles or []:
            self.open(handle)

    def get_windows_handles( self ):
        return [view.handle() for view in self._windows]

    def open_windows( self, windows_handles ):
        for handle in windows_handles or []:
            handle.construct(self)

    def pick_arg( self, kind ):
        return None

    def get_global_commands( self ):
        return self.server_commands + self._commands

    def window_created( self, view ):
        self._windows.append(view)

    def window_closed( self, view ):
        self._windows.remove(view)
        if not self._windows:
            self.save_state([view.handle()])

    def open_in_any_window( self, handle ):
        self._windows[0].get_current_view().open(handle)

    @command('Quit', 'Quit application', 'Alt+Q')
    def quit( self ):
        ## module.set_shutdown_flag()
        self.save_state(self.get_windows_handles())
        QtGui.QApplication.quit()

    def save_state( self, state ):
        with file(STATE_FILE_PATH, 'wb') as f:
            f.write(pickle_dumps(state))

    def load_state( self ):
        try:
            with file(STATE_FILE_PATH, 'rb') as f:
                return pickle_loads(f.read())
        except (EOFError, IOError, IndexError) as x:
            print 'Error loading state:', x
            return None


class OpenRespHandler(proxy_registry.RespHandler):

    def __init__( self, app ):
        self.app = app

    def process_response( self, response ):
        handle = response.get_handle2open()
        self.app.open_in_any_window(handle)


def main():
    if len(sys.argv) > 1:
        path = dict(pair.split('=') for pair in sys.argv[1].split(','))  # module=file,fspath=/usr/portabe
    else:
        path=dict(
            module='file',
            fspath=os.path.expanduser('~'))

    server_commands = []  # todo
    app = Application(server_commands)

    server = Server(('localhost', 8888))

    resp_handler = OpenRespHandler(app)
    get_request = dict(method='get', path=path, request_id=1)
    commands_response = server.execute_request(get_request, resp_handler)

    ## handle = server.request_an_object(get_request)
    handle = text_view.Handle(text_object.TextObject('hello'))

    ## commands_request = dict(method='get_commands', request_id=2)
    ## commands_response = server.execute_request(commands_request, resp_handler)
    ## server_commands = [ModuleCommand.from_json(cmd) for cmd in commands_response.result.commands]

    windows_handles = app.load_state()
    print 'loaded state: ', windows_handles

    #obj = fsopen('/tmp')
    #obj = process.Process('/usr', 'find')
    #obj = process.Process('/usr/portage', 'ls -l')
    #obj = process.Process('/usr/portage', 'i=0; while [ $i -lt 50 ]; do sleep 1; echo -n "-$i-"; i=$(($i+1)); if [ $(($i%10)) -eq 0 ]; then echo; fi; done')
    #obj = process.Process('/usr/portage', 'nohup /bin/bash -e "i=0; while [ $i -lt 10000 ]; do sleep 0.01; echo -n "-$i-"; i=$(($i+1)); if [ $(($i%10)) -eq 0 ]; then echo; fi; done"')
    #obj = process.ProcessList(process.module)
    #obj = file_view.File(os.path.expanduser('~/tmp/numbered.txt'))
    #obj = file_view.File('list_view.py')

    if not windows_handles:
        handle = window.Handle(
            tab_view.Handle([
                navigator.Handle(
                    handle)]))
        windows_handles = [handle]

    app.open_windows(windows_handles)
    app.exec_()

main()
