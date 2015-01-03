#!/usr/bin/env python

import sys
import os
import os.path
import stat
import traceback
import json_connection


LISTEN_PORT = 8888
MIN_ROWS_RETURNED = 10


class Column(object):

    def __init__( self, id, title ):
        self.id = id
        self.title = title

    def as_json( self ):
        return dict(
            id=self.id,
            title=self.title,
            )


class Element(object):

    def __init__( self, key, row, commands ):
        self.key = key
        self.row = row  # value list
        self.commands = commands

    def as_json( self ):
        return dict(
            row=self.row,
            commands=[cmd.as_json() for cmd in self.commands],
            )


class Command(object):

    def __init__( self, id, text, desc, shortcut=None ):
        self.id = id
        self.text = text
        self.desc = desc
        self.shortcut = shortcut

    def as_json( self ):
        return dict(
            id=self.id,
            text=self.text,
            desc=self.desc,
            shortcut=self.shortcut,
            )


class Dir(object):

    columns = [
        Column('key', 'File Name'),
        Column('ftype', 'File type'),
        Column('ftime', 'Modification time'),
        Column('fsize', 'File size'),
        ]

    def __init__( self, fspath ):
        self.fspath = os.path.abspath(fspath)
        self.path = '/fs/' + fspath.lstrip('/')
        for idx, column in enumerate(self.columns):
            if column.id == 'key':
                self.key_column_idx = idx
                break
        else:
            assert False, 'Unknown column id: %r' % slef.key_column_id

    def get_elements( self, count=None, from_key=None ):
        elements = self.get_all_elements()
        from_idx = 0
        if from_key is not None:
            for idx, elt in enumerate(elements):
                if elt.row[self.key_column_idx] == from_key:
                    from_idx = idx + 1
                    break
            else:
                print 'Warning: unknown "from_key" is requested: %r' % from_key
        return elements[from_idx:from_idx + max(count or 0, MIN_ROWS_RETURNED)]

    def get_all_elements( self ):
        dirs  = []
        files = []
        try:
            names = os.listdir(self.fspath)
        except OSError:  # path may be invalid
            names = []
        for fname in names:
            fname = fsname2uni(fname)
            if fname[0] == '.': continue  # skip special and hidden names
            fspath = os.path.join(self.fspath, fname)
            finfo = self.get_file_info(fname, fspath)
            if finfo['ftype'] == 'dir':
                dirs.append(finfo)
            else:
                files.append(finfo)
        def key( finfo ):
            return finfo['key']
        return map(self.make_elt, sorted(dirs, key=key) + sorted(files, key=key))

    def get_file_info( self, fname, fspath ):
        s = os.stat(fspath)
        return dict(
            key=fname,
            ftype='dir' if os.path.isdir(fspath) else 'file',
            ftime=s[stat.ST_MTIME],
            fsize=s[stat.ST_SIZE],
            )
 
    def make_elt( self, finfo ):
        row = [finfo[column.id] for column in self.columns]
        return Element(finfo['key'], row, commands=self.elt_commands(finfo))

    def elt_commands( self, finfo ):
        if finfo['ftype'] == 'dir':
            return [Command('open', 'Open', 'Open directory')]
        else:
            return []

    def run_element_command( self, command_id, element_key ):
        assert command_id == 'open', repr(command_id)
        elt_fname = element_key
        fspath = os.path.join(self.fspath, elt_fname)
        return Dir(fspath)

    def run_dir_command( self, command_id ):
        assert command_id == 'parent', repr(command_id)
        fspath = self.get_parent_dir()
        if fspath is not None:
            return Dir(fspath)

    def get_parent_dir( self ):
        dir = os.path.dirname(self.fspath)
        if dir == self.fspath:
            return None  # already root
        return dir

    def dir_commands( self ):
        return [Command('parent', 'Open parent', 'Open parent directory', 'Ctrl+Backspace')]


if sys.platform == 'win32':
    fs_encoding = sys.getfilesystemencoding()
else:
    fs_encoding = 'utf-8'

def fsname2uni( v ):
    if type(v) is unicode:
        return v
    else:
       return unicode(v, fs_encoding)


class Server(object):

    init_dir = Dir(os.path.expanduser('~/'))

    def resolve( self, path ):
        assert path.startswith('/fs/')
        fspath = path[3:]
        return Dir(fspath)

    def resp_elements( self, dir, count=None, key=None ):
        return [elt.as_json() for elt in dir.get_elements(count, key)]

    def resp_object( self, dir ):
        return dict(
            path=dir.path,
            dir_commands=[cmd.as_json() for cmd in dir.dir_commands()],
            columns=[column.as_json() for column in dir.columns],
            elements=self.resp_elements(dir))

    def process_request( self, request ):
        method = request['method']
        if method == 'init':
            return self.resp_object(self.init_dir)
        path = request['path']
        dir = self.resolve(path)
        if method == 'get_elements':
            key = request['key']
            count = request['count']
            return dict(elements=self.resp_elements(dir, count, key))
        elif method == 'element_command':
            command_id = request['command_id']
            element_key = request['element_key']
            new_dir = dir.run_element_command(command_id, element_key)
            return self.resp_object(new_dir)
        elif method == 'dir_command':
            command_id = request['command_id']
            new_dir = dir.run_dir_command(command_id)
            return self.resp_object(new_dir)
        else:
            assert False, repr(method)

    def run( self, connection, cln_addr ):
        print 'accepted connection from %s:%d' % cln_addr
        try:
            row_count = 0
            rpc_count = 0
            while True:
                request = connection.receive()
                print 'request: %r' % request
                response = self.process_request(request)
                connection.send(response)
        except json_connection.Error as x:
            print x
        except:
            traceback.print_exc()
            


def main():
    server = json_connection.Server(LISTEN_PORT, Server().run)
    server.run()


main()
