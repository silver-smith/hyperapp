import logging

import docutils_tinyhtml
import docutils.core
from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    )
from .code.mark import mark
from .code.view import View

log = logging.getLogger(__name__)


class StaticWikiAdapter:

    @classmethod
    @mark.actor.ui_adapter_creg
    def from_piece(cls, piece, model, ctx):
        return cls(model)

    def __init__(self, wiki):
        self._wiki = wiki

    @property
    def model(self):
        return self._wiki

    def get_text(self):
        return self._wiki.text

    def text_to_value(self, text):
        return text

    def value_changed(self, new_value):
        if new_value == self._wiki:
            return
        log.debug("Static wiki adapter: Ignoring new value: %r", new_value)


@mark.actor.resource_name_creg
def static_wiki_adapter_resource_name(piece, gen):
    return 'static_wiki_adapter'


class WikiTextView(View):

    @classmethod
    @mark.view
    def from_piece(cls, piece, model, ctx, ui_adapter_creg):
        adapter = ui_adapter_creg.invite(piece.adapter, model, ctx)
        return cls(piece.adapter, adapter)

    def __init__(self, adapter_ref, adapter):
        super().__init__()
        self._adapter_ref = adapter_ref
        self._adapter = adapter

    @property
    def piece(self):
        return htypes.wiki.text_view(
            adapter=self._adapter_ref,
            )

    def construct_widget(self, state, ctx):
        w = QtWidgets.QTextBrowser(
            openLinks=False,
            )
        w.setHtml(self._text_to_html(self._adapter.get_text()))
        w.anchorClicked.connect(self._on_anchor_clicked)
        return w

    def widget_state(self, widget):
        return htypes.wiki.state()

    def primary_parent_context(self, rctx, widget):
        return rctx.clone_with(
            model_state=self._model_state(widget),
            )

    def _model_state(self, widget):
        return self.get_value(widget)

    def get_plain_text(self, widget):
        return widget.toPlainText()

    def get_value(self, widget):
        text = self.get_plain_text(widget)
        return self._adapter.text_to_value(text)

    def _on_anchor_clicked(self, url):
        log.info('Wiki text view: Anchor clicked: url.path=%r', url.path())

    def _text_to_html(self, text):
        return docutils.core.publish_string(
            text,
            writer=docutils_tinyhtml.Writer(),
            writer_name='html',
            ).decode()


class WikiView(WikiTextView):

    @property
    def piece(self):
        return htypes.wiki.wiki_view(
            adapter=self._adapter_ref,
            )

    def _on_anchor_clicked(self, url):
        log.info('Wiki view: Anchor clicked: url.path=%r', url.path())



@mark.view_factory.model_t
def wiki_text(piece, adapter=None):
    if adapter is None:
        adapter = htypes.str_adapter.static_str_adapter()
    return htypes.wiki.text_view(
        adapter=mosaic.put(adapter),
        )


@mark.view_factory.model_t
def wiki(piece, adapter=None):
    if adapter is None:
        adapter = htypes.str_adapter.static_str_adapter()
    return htypes.wiki.wiki_view(
        adapter=mosaic.put(adapter),
        )
