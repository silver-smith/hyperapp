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


class Element(object):

    def __init__( self, key, row, commands ):
        self.key = key
        self.row = row  # value list
        self.commands = commands


class Dir(object):

    columns = [
        Column('key', 'File Name'),
        Column('ftype', 'File type'),
        Column('ftime', 'Modification time'),
        Column('fsize', 'File size'),
        ]

    def __init__( self, fspath ):
        self.fspath = fspath
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
        return Element(finfo['key'], row, commands=[])

        


if sys.platform == 'win32':
    fs_encoding = sys.getfilesystemencoding()
else:
    fs_encoding = 'utf-8'

def fsname2uni( v ):
    if type(v) is unicode:
        return v
    else:
       return unicode(v, fs_encoding)


def server_fn( connection, cln_addr ):
    dir = Dir('/usr/portage/distfiles')
    print 'accepted connection from %s:%d' % cln_addr
    try:
        row_count = 0
        rpc_count = 0
        while True:
            request = connection.receive()
            print 'request: %r' % request
            method = request['method']
            if method == 'load':
                response = dict(
                    columns=[dict(id=column.id, title=column.title) for column in dir.columns],
                    rows=[elt.row for elt in dir.get_elements()])
            elif method == 'get_rows':
                key = request['key']
                count = request['count']
                response=dict(
                    rows=[elt.row for elt in dir.get_elements(count, key)])
            else:
                response = None
            connection.send(response)
    except json_connection.Error as x:
        print x
    except:
        traceback.print_exc()
            


def main():
    server = json_connection.Server(LISTEN_PORT, server_fn)
    server.run()


main()
