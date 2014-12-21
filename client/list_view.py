import sys
from PySide import QtCore, QtGui

sys.path.append('..')

import json_connection


class Column(object):

    def __init__( self, idx, id, title ):
        self.idx = idx
        self.id = id
        self.title = title



class Element(object):

    def __init__( self, row, commands ):
        self.row = row
        self.commands = commands


class ElementList(object):

    def __init__( self, connection, key_column_idx, initial_elements ):
        self.conn = connection
        self.elements = initial_elements
        self.key_column_idx = key_column_idx

    def element_count( self ):
        return len(self.elements)

    def ensure_element_count( self, element_count ):
        if element_count < self.element_count(): return
        self.load_elements(element_count - self.element_count())

    def load_elements( self, load_count ):
        last_key = self.elements[-1].row[self.key_column_idx]
        self.conn.send(dict(method='get_elements',
                            key=last_key,
                            count=load_count))
        response = self.conn.receive()
        self.elements += [Element(elt['row'], elt['commands']) for elt in response['elements']]


class Model(QtCore.QAbstractTableModel):

    def __init__( self, element_list, visible_columns ):
        QtCore.QAbstractTableModel.__init__(self)
        self.element_list = element_list
        self.visible_columns = visible_columns

    def element_count( self ):
        return self.element_list.element_count()

    def elements_added( self, added_count ):
        print 'ensure_element_count, self.element_count() =', self.element_count(), ', count = ', added_count
        element_count = self.element_list.element_count()
        self.rowsInserted.emit(QtCore.QModelIndex(), element_count - added_count, element_count - 1)

    def data( self, index, role ):
        if role == QtCore.Qt.DisplayRole:
            element = self.element_list.elements[index.row()]
            column = self.visible_columns[index.column()]
            return element.row[column.idx]
        return None

    def headerData( self, section, orient, role ):
        if role == QtCore.Qt.DisplayRole and orient == QtCore.Qt.Orientation.Horizontal:
            return self.visible_columns[section].title
        hdata = QtCore.QAbstractTableModel.headerData(self, section, orient, role)
        return hdata

    def rowCount( self, parent ):
        if parent == QtCore.QModelIndex() and self.element_list:
            return self.element_list.element_count()
        else:
            return 0

    def columnCount( self, parent ):
        if parent == QtCore.QModelIndex() and self.element_list:
            return len(self.visible_columns)
        else:
            return 0

    def __del__( self ):
        print '~Model'


class View(QtGui.QTableView):

    def __init__( self, connection, response ):
        QtGui.QTableView.__init__(self)
        self.connection = connection
        self.columns = None
        self.element_list = None
        self._model = Model(element_list=None, visible_columns=None)
        self.setModel(self._model)
        self.verticalHeader().hide()
        opts = self.viewOptions()
        self.verticalHeader().setDefaultSectionSize(QtGui.QFontInfo(opts.font).pixelSize() + 4)
        self.horizontalHeader().setStretchLastSection(True)
        self.setShowGrid(False)
        self.verticalScrollBar().valueChanged.connect(self.vscrollValueChanged)
        self.set_object(response)

    def set_object( self, response ):
        elements = [Element(elt['row'], elt['commands']) for elt in response['elements']]
        columns = [Column(idx, d['id'], d['title']) for idx, d in enumerate(response['columns'])]
        visible_columns = filter(lambda column: column.title is not None, columns)
        self.model().beginResetModel()
        self.columns = columns
        self.element_list = ElementList(self.connection, self._find_key_column(), elements)
        self._model.element_list = self.element_list
        self._model.visible_columns = visible_columns
        self.model().endResetModel()
        self.resizeColumnsToContents()

    def _find_key_column( self ):
        for idx, col in enumerate(self.columns):
            if col.id == 'key':
                return col.idx
        assert False, 'No "key" column'

    def vscrollValueChanged( self, value ):
        print 'vscrollValueChanged'
        first_visible_row = value
        last_visible_row = self.verticalHeader().visualIndexAt(self.viewport().height())
        print 'vscrollValueChanged, first_visible_row =', first_visible_row, \
          ', last_visible_row =', last_visible_row, \
          'viewport.height =', self.verticalHeader().logicalIndexAt(self.viewport().height())
        row_height = self.verticalHeader().defaultSectionSize()
        visible_row_count = self.viewport().height() / row_height
        self.ensure_elements(first_visible_row + visible_row_count + 1)

    def resizeEvent( self, evt ):
        result = QtGui.QTableView.resizeEvent(self, evt)
        row_height = self.verticalHeader().defaultSectionSize()
        visible_row_count = self.viewport().height() / row_height
        first_visible_row = self.verticalHeader().visualIndexAt(0)
        print 'resizeEvent, first_visible_row =', first_visible_row, ', visible_row_count =', visible_row_count
        self.ensure_elements(max(first_visible_row, 0) + visible_row_count + 1)
        return result

    def ensure_elements( self, element_count ):
        old_element_count = self.element_list.element_count()
        if element_count <= old_element_count: return
        self.element_list.load_elements(element_count - old_element_count)
        self._model.elements_added(self.element_list.element_count() - old_element_count)


def main():
    app = QtGui.QApplication(sys.argv)
    connection = json_connection.ClientConnection(('localhost', 8888))
    request = dict(method='load')
    connection.send(request)
    response = connection.receive()
    view = View(connection, response)
    view.resize(800, 300)
    view.show()
    app.exec_()

main()
