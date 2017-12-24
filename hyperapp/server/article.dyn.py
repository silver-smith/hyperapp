import logging
from pony.orm import db_session, commit, Required, Optional, Set, select
from ..common.util import encode_path, decode_path
from ..common.htypes import Column
from ..common.interface import core as core_types
from ..common.interface import article as article_types
from ..common.identity import PublicKey
from ..common.url import Url
from ..common.list_object import ListDiff
from ..common.interface import core as core_types
from .util import path_part_to_str
from .command import command
from .object import Object, SmallListObject, subscription
from .module import ModuleCommand
from .ponyorm_module import PonyOrmModule

log = logging.getLogger(__name__)


MODULE_NAME = 'article'


class Article(Object):

    mode_view = object()
    mode_edit = object()

    iface = article_types.article
    objimpl_id = 'proxy.text'
    class_name = 'article'

    class_registry = {}  # ponyorm entity class -> class

    @classmethod
    def register_class(cls, ponyorm_entity_class):
        cls.class_registry[ponyorm_entity_class] = cls

    @classmethod
    def from_rec(cls, article_rec):
        real_cls = cls.class_registry[article_rec.__class__]
        return real_cls(article_rec.id)

    @classmethod
    def resolve(cls, path):
        article_id = path.pop_int_opt(none_str='new')
        return cls(article_id)

    def __init__(self, article_id=None, mode=mode_view):
        assert mode in [self.mode_view, self.mode_edit], repr(mode)
        Object.__init__(self)
        self.article_id = article_id
        self.mode = mode

    def get_path(self):
        return this_module.make_path(self.class_name, path_part_to_str(self.article_id, none_str='new'))
        
    @db_session
    def get_contents(self, request, **kw):
        if self.article_id is not None:
            rec = this_module.Article[self.article_id]
            text = rec.text
        else:
            text = None
        return Object.get_contents(self, request, text=text, **kw)

    def get_handle(self, request):
        if self.mode == self.mode_view:
            return core_types.obj_handle('text_view', self.get(request))
        else:
            return core_types.obj_handle('text_edit', self.get(request))

    @command('save')
    def command_save(self, request):
        return self.do_save(request, request.params.text)

    @command('refs')
    def command_refs(self, request):
        return request.make_response_object(ArticleRefList(self.article_id))

    @command('open_ref')
    @db_session
    def command_open_ref(self, request):
        ref_id = request.params.ref_id
        rec = this_module.ArticleRef[ref_id]
        iface = this_module.iface_registry.resolve(rec.iface)
        path = decode_path(rec.path)
        if rec.server_public_key_pem:
            public_key = PublicKey.from_pem(rec.server_public_key_pem)
            target_url = Url(iface, public_key, path)
            return request.make_response_redirect(target_url)
        else:
            target = this_module.module_registry.run_resolver(iface, path)
            return request.make_response_object(target)

    @db_session
    def do_save(self, request, text):
        if self.article_id is not None:
            article_rec = this_module.Article[self.article_id]
            article_rec.text = text
        else:
            article_rec = this_module.Article(text=text)
        commit()
        self.article_id = article_rec.id  # now may have new get_path()
        log.info('Article is saved, article_id = %r', self.article_id)
        subscription.distribute_update(self.iface, self.get_path(), text)
        return request.make_response_result(new_path=self.get_path())


class ArticleRefList(SmallListObject):

    iface = article_types.article_ref_list
    objimpl_id = 'proxy_list'
    default_sort_column_id = 'ref_id'
    class_name = 'ref_list'

    @classmethod
    def resolve(cls, path):
        article_id = path.pop_int()
        return cls(article_id)

    def __init__(self, article_id):
        SmallListObject.__init__(self, core_types)
        self.article_id = article_id

    def get_path(self):
        return this_module.make_path(self.class_name, path_part_to_str(self.article_id))

    @command('parent')
    @db_session
    def command_parent(self, request):
        rec = this_module.Article[self.article_id]
        return request.make_response_object(Article.from_rec(rec))

    @command('open', kind='element')
    @db_session
    def command_open(self, request):
        ref_id = request.params.element_key
        rec = this_module.ArticleRef[ref_id]
        iface = this_module.iface_registry.resolve(rec.iface)
        path = decode_path(rec.path)
        if rec.server_public_key_pem:
            public_key = PublicKey.from_pem(rec.server_public_key_pem)
            target_url = Url(iface, public_key, path)
            target_handle = self._core_types.redirect_handle(view_id='redirect', redirect_to=target_url.to_data())
        else:
            target_obj = this_module.module_registry.run_resolver(iface, path)
            target_handle = target_obj.get_handle(request)
        return request.make_response_handle(target_handle)

    @command('add')
    @db_session
    def command_add(self, request):
        url = Url.from_data(this_module.iface_registry, request.params.target_url)
        server_public_key_pem, path = self._make_article_ref_url_fields(request, url)
        rec = this_module.ArticleRef(article=this_module.Article[self.article_id],
                                     iface=url.iface.iface_id,
                                     server_public_key_pem=server_public_key_pem,
                                     path=path)
        commit()
        diff = ListDiff.add_one(self.rec2element(request, rec))
        subscription.distribute_update(self.iface, self.get_path(), diff)
        handle = self.ListHandle(self.get(request), key=rec.id)
        return request.make_response_handle(handle)

    @command('update', kind='element')
    @db_session
    def command_update(self, request):
        ref_id = request.params.element_key
        url = Url.from_data(this_module.iface_registry, request.params.target_url)
        rec = this_module.ArticleRef[ref_id]
        server_public_key_pem, path = self._make_article_ref_url_fields(request, url)
        rec.server_public_key_pem = server_public_key_pem
        rec.path = path
        diff = ListDiff.replace(rec.id, self.rec2element(request, rec))
        subscription.distribute_update(self.iface, self.get_path(), diff)
        handle = self.ListHandle(self.get(request), key=rec.id)
        return request.make_response_handle(handle)

    def _make_article_ref_url_fields(self, request, url):
        if request.me.is_mine_url(url):
            server_public_key_pem = ''
        else:
            server_public_key_pem = url.public_key.to_pem()
        return (server_public_key_pem.strip(), encode_path(url.path))

    @command('delete', kind='element')
    @db_session
    def command_delete(self, request):
        ref_id = request.params.element_key
        this_module.ArticleRef[ref_id].delete()
        diff = ListDiff.delete(ref_id)
        subscription.distribute_update(self.iface, self.get_path(), diff)

    @db_session
    def fetch_all_elements(self, request):
        return [self.rec2element(request, rec) for rec in
                select(ref for ref in this_module.ArticleRef
                       if ref.article==this_module.Article[self.article_id])
                       .order_by(this_module.ArticleRef.id)]

    @classmethod
    def rec2element(cls, request, rec):
        commands = [cls.command_open, cls.command_update, cls.command_delete]
        if not rec.server_public_key_pem:
            public_key = request.me.get_public_key()
            url_title = '<local>:%s' % rec.path
        else:
            public_key = PublicKey.from_pem(rec.server_public_key_pem)
            url_title = '%s:%s' % (public_key.get_short_id_hex(), rec.path)
        iface = this_module.iface_registry.resolve(rec.iface)
        path = decode_path(rec.path)
        url = Url(iface, public_key, path)
        return cls.Element(cls.Row(rec.id, url.to_str(), url_title), commands)


class ThisModule(PonyOrmModule):

    def __init__(self, services):
        PonyOrmModule.__init__(self, MODULE_NAME)
        self.module_registry = services.module_registry
        self.iface_registry = services.iface_registry
        self.article_fields = dict(text=Required(str),
                                   refs=Set('ArticleRef'))

    def init_phase2(self):
        self.Article = self.make_entity('Article', **self.article_fields)
        self.ArticleRef = self.make_entity('ArticleRef',
                                           article=Required(self.Article),
                                           title=Required(str),
                                           href=Required(bytes),
                                           )
        Article.register_class(self.Article)

    def resolve(self, iface, path):
        objname = path.pop_str()
        if objname == Article.class_name:
            return Article.resolve(path)
        if objname == ArticleRefList.class_name:
            return ArticleRefList.resolve(path)
        path.raise_not_found()

    def get_commands(self):
        return [ModuleCommand('create', 'Create article', 'Create new article', 'Alt+A', self.name)]

    def run_command(self, request, command_id):
        if command_id == 'create':
            return request.make_response_object(Article(mode=Article.mode_edit))
        return PonyOrmModule.run_command(self, request, command_id)

    def add_article_fields(self, **fields):
        self.article_fields.update(fields)
