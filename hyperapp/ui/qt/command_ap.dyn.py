import re


class ShortcutAp:

    def __init__(self, used_shortcuts):
        self._used_shortcuts = used_shortcuts

    def apply(self, widget, value):
        if value in self._used_shortcuts:
            return False
        widget.setShortcut(value)
        self._used_shortcuts.add(value)
        return True

    def clear(self, widget):
        widget.setShortcut('')


class ButtonShortcutAp(ShortcutAp):

    def apply(self, widget, value):
        if value in self._used_shortcuts:
            return False
        text = widget.text()
        mo = re.match(r'(.+) \(.+\)', text)
        if mo:
            text = mo[1]
        widget.setText(f'{text} ({value})')
        widget.setShortcut(value)
        self._used_shortcuts.add(value)
        return True

    def clear(self, widget):
        widget.setShortcut('')
