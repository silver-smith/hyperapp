import asyncio
import logging

import docutils_tinyhtml
import docutils.core
from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    web,
    )
from .code.mark import mark
from .code.remote_model import real_model_t
from .code.view import View

log = logging.getLogger(__name__)


class WikiToTextConvertor:

    @classmethod
    @mark.actor.convertor_creg
    def from_piece(cls, piece):
        return cls()

    def value_to_view(self, value):
        return value.text

    def view_to_value(self, old_value, view_value):
        return htypes.wiki.wiki(
            text=view_value,
            refs=old_value.refs,
            )


@mark.actor.resource_name_creg
def wiki_convertor_resource_name(piece, gen):
    return 'wiki_to_string_convertor'


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
        w.setHtml(self._text_to_html(self._get_text()))
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
        return self._adapter.view_to_value(text)

    def _get_text(self):
        return self._adapter.get_value()

    def _on_anchor_clicked(self, url):
        log.info('Wiki text view: Anchor clicked: url.path=%r', url.path())

    def _text_to_html(self, text):
        return docutils.core.publish_string(
            text,
            writer=docutils_tinyhtml.Writer(),
            writer_name='html',
            ).decode()


class WikiView(WikiTextView):

    @classmethod
    @mark.view
    def from_piece(cls, piece, model, ctx, ui_adapter_creg, view_reg, visualizer):
        adapter = ui_adapter_creg.invite(piece.adapter, model, ctx)
        return cls(view_reg, visualizer, piece.adapter, adapter, ctx)

    def __init__(self, view_reg, visualizer, adapter_ref, adapter, ctx):
        super().__init__(adapter_ref, adapter)
        self._view_reg = view_reg
        self._visualizer = visualizer
        self._ctx = ctx

    @property
    def piece(self):
        return htypes.wiki.wiki_view(
            adapter=self._adapter_ref,
            )

    def _get_text(self):
        return self._adapter.get_value().text

    def _on_anchor_clicked(self, url):
        log.info('Wiki view: Anchor clicked: url.path=%r', url.path())
        asyncio.create_task(self._open_ref(url.path()))

    async def _open_ref(self, ref_id):
        target_ref = self._get_ref(ref_id)
        model = web.summon(target_ref)
        log.info('Wiki view: Open target: %r', model)
        navigator_rec = self._ctl_hook.navigator
        navigator_w = navigator_rec.widget_wr()
        if navigator_w is None:
            raise RuntimeError("Navigator widget is gone")
        view_piece = await self._visualizer(self._ctx, real_model_t(model))
        model_ctx = self._ctx.clone_with(model=model)
        view = self._view_reg.animate(view_piece, model_ctx)
        log.info("Wiki view: visualizing with view: %s", view)
        await navigator_rec.view.open(self._ctx, model, view, navigator_w)

    def _get_ref(self, ref_id):
        wiki = self._adapter.get_value()
        id_to_ref = {
          ref.id: ref.target
          for ref in wiki.refs
          }
        return id_to_ref[ref_id]


@mark.view_factory.model_t(htypes.wiki.wiki)
def wiki_text(accessor):
    cvt = htypes.wiki.wiki_to_string_convertor()
    adapter = htypes.value_adapter.value_adapter(
        accessor=mosaic.put(accessor),
        convertor=mosaic.put(cvt),
        )
    return htypes.wiki.text_view(
        adapter=mosaic.put(adapter),
        )


@mark.view_factory.model_t(htypes.wiki.wiki)
def wiki(accessor):
    adapter = htypes.value_adapter.value_adapter(
        accessor=mosaic.put(accessor),
        convertor=mosaic.put(htypes.type_convertor.noop_convertor()),
        )
    return htypes.wiki.wiki_view(
        adapter=mosaic.put(adapter),
        )
