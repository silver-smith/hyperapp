import sys
import os
import os.path
import stat
from operator import attrgetter, itemgetter

from . import htypes


MIN_ROWS_RETURNED = 100


def rows2fetched_chunk(key_attribute, all_rows, fetch_request, Chunk):
    sorted_rows = sorted(all_rows, key=attrgetter(fetch_request.sort_column_id))
    if fetch_request.from_key is None:
        idx = 0
    else:
        for idx, row in enumerate(sorted_rows):
            if getattr(row, key_attribute) > fetch_request.from_key:
                break
        else:
            idx = len(sorted_rows)
    start = max(0, idx - fetch_request.desc_count)
    end = idx + fetch_request.asc_count
    if end - start < MIN_ROWS_RETURNED:
        end = start + MIN_ROWS_RETURNED
        if end < idx + 1:
            end = idx + 1
    if end > len(sorted_rows):
        end = len(sorted_rows)
    rows = sorted_rows[start:end]
    bof = start == 0
    eof = end == len(sorted_rows)
    return Chunk(fetch_request.sort_column_id, fetch_request.from_key, rows, bof, eof)


class FsServiceImpl(object):

    def __init__(self):
        if sys.platform == 'win32':
            self._fs_encoding = sys.getfilesystemencoding()
        else:
            self._fs_encoding = 'utf-8'

    def fetch_dir_contents(self, fs_path, fetch_request):
        all_rows = self._fetch_dir_contents(fs_path)
        return rows2fetched_chunk('key', all_rows, fetch_request, htypes.fs.fs_dir_chunk)

    def _fetch_dir_contents(self, fs_path):
        dir_path = '/' + '/'.join(fs_path)
        dirs  = []
        files = []
        try:
            names = os.listdir(dir_path)
        except OSError:  # path may be invalid
            names = []
        for fname in names:
            fname = self._fsname2unicode(fname)
            if fname[0] == '.': continue  # skip special and hidden names
            item_fs_path = os.path.join(dir_path, fname)
            finfo = self._get_file_info(fname, item_fs_path)
            if finfo['ftype'] == 'dir':
                dirs.append(finfo)
            else:
                files.append(finfo)
        return [htypes.fs.fs_dir_row(key=finfo['key'], ftype=finfo['ftype'], ftime=finfo['ftime'], fsize=finfo['fsize'])
                for finfo in sorted(dirs, key=itemgetter('key')) +
                             sorted(files, key=itemgetter('key'))]

    def _get_file_info(self, fname, fspath):
        try:
            s = os.stat(fspath)
        except OSError:
            return dict(
                key=fname,
                ftype='file',
                ftime=0,
                fsize=0)
        return dict(
            key=fname,
            ftype='dir' if os.path.isdir(fspath) else 'file',
            ftime=s[stat.ST_MTIME],
            fsize=s[stat.ST_SIZE],
            )

    def _fsname2unicode(self, value):
        if type(value) is str:
            return value
        else:
            return str(value, self._fs_encoding)
