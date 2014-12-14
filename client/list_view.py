import sys
from PySide import QtCore, QtGui

sys.path.append('..')

import json_connection


class RowList(object):

    def __init__( self, connection, initial_rows ):
        self.conn = connection
        self.rows = initial_rows

    def row_count( self ):
        return len(self.rows)

    def ensure_row_count( self, row_count ):
        if row_count < self.row_count(): return
        self.load_rows(row_count - self.row_count())

    def load_rows( self, load_count ):
        self.conn.send(dict(method='get_rows', args=[load_count]))
        response = self.conn.receive()
        self.rows.extend(response['rows'])


class Model(QtCore.QAbstractTableModel):

    def __init__( self, row_list ):
        QtCore.QAbstractTableModel.__init__(self)
        self.row_list = row_list

    def row_count( self ):
        return self.row_list.row_count()

    def rows_added( self, added_count ):
        print 'ensure_row_count, self.row_count() =', self.row_count(), ', count = ', added_count
        row_count = self.row_list.row_count()
        self.rowsInserted.emit(QtCore.QModelIndex(), row_count - added_count, row_count - 1)

    def data( self, index, role ):
        if role == QtCore.Qt.DisplayRole:
            return self.row_list.rows[index.row()][index.column()]
        return None

    def headerData( self, section, orient, role ):
        if role == QtCore.Qt.DisplayRole and orient == QtCore.Qt.Orientation.Horizontal:
            return 'header#%d' % section
        hdata = QtCore.QAbstractTableModel.headerData(self, section, orient, role)
        return hdata

    def rowCount( self, parent ):
        if parent == QtCore.QModelIndex():
            return self.row_list.row_count()
        else:
            return 0

    def columnCount( self, parent ):
        if parent == QtCore.QModelIndex():
            return 5
        else:
            return 0

    def __del__( self ):
        print '~Model'


class View(QtGui.QTableView):

    def __init__( self, connection, initial_rows ):
        QtGui.QTableView.__init__(self)
        self.row_list = RowList(connection, initial_rows)
        self._model = Model(self.row_list)
        self.setModel(self._model)
        self.verticalHeader().hide()
        opts = self.viewOptions()
        self.verticalHeader().setDefaultSectionSize(QtGui.QFontInfo(opts.font).pixelSize() + 4)
        self.horizontalHeader().setStretchLastSection(True)
        self.setShowGrid(False)
        self.verticalScrollBar().valueChanged.connect(self.vscrollValueChanged)

    def vscrollValueChanged( self, value ):
        print 'vscrollValueChanged'
        first_visible_row = value
        last_visible_row = self.verticalHeader().visualIndexAt(self.viewport().height())
        print 'vscrollValueChanged, first_visible_row =', first_visible_row, \
          ', last_visible_row =', last_visible_row, \
          'viewport.height =', self.verticalHeader().logicalIndexAt(self.viewport().height())
        row_height = self.verticalHeader().defaultSectionSize()
        visible_row_count = self.viewport().height() / row_height
        self.ensure_rows(first_visible_row + visible_row_count + 1)

    def resizeEvent( self, evt ):
        result = QtGui.QTableView.resizeEvent(self, evt)
        row_height = self.verticalHeader().defaultSectionSize()
        visible_row_count = self.viewport().height() / row_height
        first_visible_row = self.verticalHeader().visualIndexAt(0)
        print 'resizeEvent, first_visible_row =', first_visible_row, ', visible_row_count =', visible_row_count
        self.ensure_rows(max(first_visible_row, 0) + visible_row_count + 1)
        return result

    def ensure_rows( self, row_count ):
        old_row_count = self.row_list.row_count()
        if row_count <= old_row_count: return
        self.row_list.load_rows(row_count - old_row_count)
        self._model.rows_added(self.row_list.row_count() - old_row_count)


def main():
    app = QtGui.QApplication(sys.argv)
    connection = json_connection.ClientConnection(('localhost', 8888))
    request = dict(method='load')
    connection.send(request)
    response = connection.receive()
    initial_rows = response['initial_rows']
    view = View(connection, initial_rows)
    view.resize(800, 300)
    view.show()
    app.exec_()

main()
