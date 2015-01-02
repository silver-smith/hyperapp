import sys
from PySide import QtCore, QtGui

sys.path.append('..')

import json_connection


class Column(object):

    def __init__( self, idx, id, title ):
        self.idx = idx
        self.id = id
        self.title = title

    @classmethod
    def from_json( cls, idx, data ):
        return cls(idx, data['id'], data['title'])


class Command(object):

    def __init__( self, id, text, desc ):
        self.id = id
        self.text = text
        self.desc = desc

    @classmethod
    def from_json(cls, data ):
        return cls(data['id'], data['text'], data['desc'])


class Element(object):

    def __init__( self, row, commands ):
        self.row = row
        self.commands = commands

    @classmethod
    def from_json( cls, data ):
        return cls(data['row'], [Command.from_json(cmd) for cmd in data['commands']])


class ListObj(object):

    def __init__( self, connection, response ):
        self.connection = connection
        self.columns = [Column.from_json(idx, column) for idx, column in enumerate(response['columns'])]
        self.elements = [Element.from_json(elt) for elt in response['elements']]
        self.key_column_idx = self._find_key_column(self.columns)

    def element_count( self ):
        return len(self.elements)

    def ensure_element_count( self, element_count ):
        if element_count < self.element_count(): return
        self.load_elements(element_count - self.element_count())

    def load_elements( self, load_count ):
        last_key = self.elements[-1].row[self.key_column_idx]
        self.connection.send(dict(method='get_elements',
                            key=last_key,
                            count=load_count))
        response = self.connection.receive()
        self.elements += [Element.from_json(elt) for elt in response['elements']]

    def element_command( self, command_id, element_key ):
        self.connection.send(dict(
            method='element_command',
            command_id=command_id,
            element_key=element_key))
        response = self.connection.receive()
        path = response['path']
        return ListObj(self.connection, response)

    def _find_key_column( self, columns ):
        for idx, col in enumerate(columns):
            if col.id == 'key':
                return col.idx
        assert False, 'No "key" column'


class Model(QtCore.QAbstractTableModel):

    def __init__( self, list_obj, visible_columns ):
        QtCore.QAbstractTableModel.__init__(self)
        self.list_obj = list_obj
        self.visible_columns = visible_columns

    def element_count( self ):
        return self.list_obj.element_count()

    def elements_added( self, added_count ):
        print 'ensure_element_count, self.element_count() =', self.element_count(), ', count = ', added_count
        element_count = self.list_obj.element_count()
        self.rowsInserted.emit(QtCore.QModelIndex(), element_count - added_count, element_count - 1)

    def data( self, index, role ):
        if role == QtCore.Qt.DisplayRole:
            element = self.list_obj.elements[index.row()]
            column = self.visible_columns[index.column()]
            return element.row[column.idx]
        return None

    def headerData( self, section, orient, role ):
        if role == QtCore.Qt.DisplayRole and orient == QtCore.Qt.Orientation.Horizontal:
            return self.visible_columns[section].title
        hdata = QtCore.QAbstractTableModel.headerData(self, section, orient, role)
        return hdata

    def rowCount( self, parent ):
        if parent == QtCore.QModelIndex() and self.list_obj:
            return self.list_obj.element_count()
        else:
            return 0

    def columnCount( self, parent ):
        if parent == QtCore.QModelIndex() and self.list_obj:
            return len(self.visible_columns)
        else:
            return 0

    def __del__( self ):
        print '~Model'


class View(QtGui.QTableView):

    def __init__( self, list_obj ):
        QtGui.QTableView.__init__(self)
        self.columns = None
        self.list_obj = None
        self._model = Model(list_obj=None, visible_columns=None)
        self.setModel(self._model)
        self.verticalHeader().hide()
        opts = self.viewOptions()
        self.verticalHeader().setDefaultSectionSize(QtGui.QFontInfo(opts.font).pixelSize() + 4)
        self.horizontalHeader().setStretchLastSection(True)
        self.setShowGrid(False)
        self.verticalScrollBar().valueChanged.connect(self.vscrollValueChanged)
        self.activated.connect(self._on_activated)
        self.set_object(list_obj)

    def set_object( self, list_obj ):
        self.model().beginResetModel()
        self.list_obj = list_obj
        self.columns = list_obj.columns
        visible_columns = filter(lambda column: column.title is not None, self.columns)
        self.key_column_idx = list_obj.key_column_idx
        self._model.list_obj = self.list_obj
        self._model.visible_columns = visible_columns
        self.model().endResetModel()
        self.resizeColumnsToContents()

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
        old_element_count = self.list_obj.element_count()
        if element_count <= old_element_count: return
        self.list_obj.load_elements(element_count - old_element_count)
        self._model.elements_added(self.list_obj.element_count() - old_element_count)

    def _on_activated( self, index ):
        elt = self.list_obj.elements[index.row()]
        for cmd in elt.commands:
            if cmd.id == 'open':
                self.open_element(elt)
                return

    def open_element( self, elt ):
        list_obj = self.list_obj.element_command('open', elt.row[self.key_column_idx])
        if list_obj:
            self.set_object(list_obj)


def main():
    app = QtGui.QApplication(sys.argv)
    connection = json_connection.ClientConnection(('localhost', 8888))
    request = dict(method='load')
    connection.send(request)
    response = connection.receive()
    list_obj = ListObj(connection, response)
    view = View(list_obj)
    view.resize(800, 300)
    view.show()
    app.exec_()

main()
