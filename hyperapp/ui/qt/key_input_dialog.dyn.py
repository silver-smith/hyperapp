import logging

from PySide6 import QtCore, QtGui, QtWidgets

log = logging.getLogger(__name__)


class KeyInputDialog(QtWidgets.QDialog):

    _key_modifiers = {
        QtCore.Qt.ShiftModifier: 'Shift',
        QtCore.Qt.ControlModifier: 'Ctrl',
        QtCore.Qt.AltModifier: 'Alt',
        QtCore.Qt.MetaModifier: 'Meta',
        }

    def __init__(self):
        super().__init__(
            windowTitle="Shortcut input",
            minimumWidth=300,
            )
        self.input_line = QtWidgets.QLineEdit(
            readOnly=True,
            )
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel("Press a key:"))
        layout.addWidget(self.input_line)
        self.setLayout(layout)
        # Do not eat Delete (and some other?) keys:
        self.input_line.setFocusPolicy(QtCore.Qt.NoFocus)
        self.key_result = None

    def keyPressEvent(self, event):
        log.debug("Key pressed: %s %s", event, self._key_event_to_str(event))
        super().keyPressEvent(event)
        if self._is_modifier(event):
            text = self._modifiers_to_str(event.modifiers()) + '+'
        else:
            text = self._key_event_to_str(event)
        self.input_line.setText(text)
        if not self._is_modifier(event) and event.key() != QtCore.Qt.Key_Escape:
            self.key_result = text
            # Let chosen key be shown for a while before closing.
            QtCore.QTimer.singleShot(200, self.close)

    def keyReleaseEvent(self, event):
        log.debug("Key released: %s %s", event, self._key_event_to_str(event))
        super().keyReleaseEvent(event)
        if not self.key_result:
            text = self._modifiers_to_str(event.modifiers())
            if text:
                text += '+'
            self.input_line.setText(text)

    @classmethod
    def _modifiers_to_str(cls, modifiers):
        name_list = [
            name
            for id, name in cls._key_modifiers.items()
            if modifiers & id
            ]
        return '+'.join(name_list)

    @staticmethod
    def _is_modifier(event):
        return event.key() in [QtCore.Qt.Key_Shift, QtCore.Qt.Key_Control, QtCore.Qt.Key_Alt, QtCore.Qt.Key_Meta]

    @staticmethod
    def _key_event_to_str(event):
        return QtGui.QKeySequence.listToString([event.keyCombination()])


def run_key_input_dialog():
    dialog = KeyInputDialog()
    dialog.exec_()
    return dialog.key_result
