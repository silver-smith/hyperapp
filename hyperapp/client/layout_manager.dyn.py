
from hyperapp.client.module import ClientModule
from .text_object import TextObject
from .text_view import TextView
from .tab_view import TabView
from .window import Window


MODULE_NAME = 'layout_manager'


class LayoutManager(object):

    def __init__(self):
        pass

    def build_default_layout(self):
        text_object = TextObject('hello')
        text_view = TextView(text_object)
        tab_view = TabView()
        tab_view.addTab(text_view, text_view.get_title())
        window = Window()
        window.setCentralWidget(tab_view)
        # window.addDockWidget(QtCore.Qt.RightDockWidgetArea, self._cmd_pane)
        window.show()
        self._window = window


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.layout_manager = LayoutManager()
