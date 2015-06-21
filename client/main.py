#!/usr/bin/env python

import sys
import os.path
import uuid
from PySide import QtCore, QtGui


sys.path.append('..')

# self-registering ifaces:
import common.interface.server_management
import common.interface.fs
import common.interface.blog
import common.interface.article

from common.interface import iface_registry
from common.request import Request
from util import pickle_dumps, pickle_loads
from server import Server
from qt_keys import key_evt2str
from view_command import command
import view
import list_view
import proxy_registry

# self-registering views:
import window
import tab_view
import navigator
import narrower
import text_object
import proxy_text_object
import text_edit
import text_view
import object_selector
import ref_list


STATE_FILE_PATH = os.path.expanduser('~/.hyperapp.state')


class Application(QtGui.QApplication, view.View):

    def __init__( self ):
        QtGui.QApplication.__init__(self, sys.argv)
        view.View.__init__(self)
        self.server = Server(('localhost', 8888))
        self._windows = []

    def get_windows_handles( self ):
        return [view.handle() for view in self._windows]

    def open_windows( self, windows_handles ):
        for handle in windows_handles or []:
            handle.construct(self)

    def pick_arg( self, kind ):
        return None

    def get_global_commands( self ):
        management_iface = iface_registry.resolve('server_management')
        management_cmd = window.OpenCommand(
            'open_server', 'Server', 'Open server global commands', 'Alt+G',
            management_iface, path=dict(module='management'))
        return [management_cmd]  + self._commands

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

    def __init__( self, iface, command_id, app ):
        proxy_registry.RespHandler.__init__(self, iface, command_id)
        self.app = app

    def process_response( self, response ):
        handle = response.result
        self.app.open_in_any_window(handle)


def main():
    if len(sys.argv) > 1:
        iface_id, path_str = sys.argv[1].split(':')
        path = dict(pair.split('=') for pair in path_str.split(','))  # module=file,fspath=/usr/portabe
    else:
        iface_id = 'fs_dir'
        path=dict(
            module='file',
            fspath=os.path.expanduser('~'))
    iface = iface_registry.resolve(iface_id)

    app = Application()

    if len(sys.argv) > 1:
        command_id = 'get'
        resp_handler = OpenRespHandler(iface, command_id, app)  # must keep explicit reference to it
        request_id = str(uuid.uuid4())
        request = Request(app.server, iface, path, command_id, request_id)
        app.server.execute_request(request, resp_handler)

    handle = text_view.Handle(text_object.TextObject('hello'))

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
    del windows_handles  # do not  keep object alive

    app.exec_()

main()
