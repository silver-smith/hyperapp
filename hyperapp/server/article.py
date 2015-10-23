from pony.orm import db_session, commit, Required, Set, select
from ..common.util import encode_url, decode_url
from ..common.interface import Command, Column, ObjHandle
from ..common.interface.article import (
    ObjSelectorHandle,
    ObjSelectorUnwrapHandle,
    article_iface,
    ref_list_iface,
    object_selector_iface,
    onwrap_object_selector_iface,
    )
from .util import path_part_to_str
from .object import Object, SmallListObject, subscription
from .module import ModuleCommand
from .ponyorm_module import PonyOrmModule


MODULE_NAME = 'article'


class Article(Object):

    mode_view = object()
    mode_edit = object()

    iface = article_iface
    objimpl_id = 'proxy.text'
    class_name = 'article'

    class_registry = {}  # ponyorm entity class -> class

    @classmethod
    def register_class( cls, ponyorm_entity_class ):
        cls.class_registry[ponyorm_entity_class] = cls

    @classmethod
    def from_rec( cls, article_rec ):
        real_cls = cls.class_registry[article_rec.__class__]
        return real_cls(article_rec.id)

    @classmethod
    def resolve( cls, path ):
        article_id = path.pop_int_opt(none_str='new')
        return cls(article_id)

    def __init__( self, article_id=None, mode=mode_view ):
        assert mode in [self.mode_view, self.mode_edit], repr(mode)
        Object.__init__(self)
        self.article_id = article_id
        self.mode = mode

    def get_path( self ):
        return module.make_path(self.class_name, path_part_to_str(self.article_id, none_str='new'))
        
    @db_session
    def get_contents( self, **kw ):
        if self.article_id is not None:
            rec = module.Article[self.article_id]
            text = rec.text
        else:
            text = None
        return Object.get_contents(self, text=text, **kw)

    def get_handle( self ):
        if self.mode == self.mode_view:
            return ObjHandle('text_view', self.get())
        else:
            return ObjHandle('text_edit', self.get())

    def get_commands( self ):
        return [
            Command('edit', 'Edit', 'Switch to edit mode', 'E'),
            Command('view', 'View', 'Finish editing, switch to view mode', 'Ctrl+F'),
            Command('save', 'Save', 'Save article', 'Ctrl+S'),
            Command('refs', 'Refs', 'Open article references', 'Ctrl+R'),
            ]

    def process_request( self, request ):
        # view and edit commands are expected to be handled by client side enterely
        if request.command_id == 'save':
            return self.run_command_save(request)
        elif request.command_id == 'refs':
            return self.run_command_refs(request)
        elif request.command_id == 'open_ref':
            return self.run_command_open_ref(request)
        else:
            return Object.process_request(self, request)

    def run_command_save( self, request ):
        return self.do_save(request, request.params.text)

    def run_command_refs( self, request ):
        return request.make_response_handle(ArticleRefList(self.article_id))

    @db_session
    def run_command_open_ref( self, request ):
        ref_id = request.params.ref_id
        rec = module.ArticleRef[ref_id]
        target_url = decode_url(rec.path)
        target_path = target_url[1:]
        target = module.run_resolver(target_path)
        return request.make_response_handle(target)

    @db_session
    def do_save( self, request, text ):
        if self.article_id is not None:
            article_rec = module.Article[self.article_id]
            article_rec.text = text
        else:
            article_rec = module.Article(text=text)
        commit()
        self.article_id = article_rec.id  # now may have new get_path()
        print 'Article is saved, article_id =', self.article_id
        subscription.distribute_update(self.iface, self.get_path(), text)
        return request.make_response_result(new_path=self.get_path())


class ArticleRefList(SmallListObject):

    iface = ref_list_iface
    objimpl_id = 'ref_list'
    default_sort_column_id = 'ref_id'
    class_name = 'ref_list'

    @classmethod
    def resolve( cls, path ):
        article_id = path.pop_int()
        return cls(article_id)

    def __init__( self, article_id ):
        SmallListObject.__init__(self)
        self.article_id = article_id

    def get_path( self ):
        return module.make_path(self.class_name, path_part_to_str(self.article_id))

    def get_commands( self ):
        return [
            Command('parent', 'Parent', 'Open parent article', 'Ctrl+Backspace'),
            Command('add', 'Add ref', 'Create new reference', 'Ins'),
            ]

    def process_request( self, request ):
        if request.command_id == 'parent':
            return self.run_command_parent(request)
        if request.command_id == 'add':
            return self.run_command_add(request)
        if request.command_id == 'open':
            return self.run_command_open(request)
        if request.command_id == 'delete':
            return self.run_element_command_delete(request)
        return SmallListObject.process_request(self, request)

    @db_session
    def run_command_parent( self, request ):
        rec = module.Article[self.article_id]
        return request.make_response_handle(Article.from_rec(rec))

    def run_command_add( self, request ):
        with db_session:
            rec = module.ArticleRef(article=module.Article[self.article_id],
                                    path=encode_url(request.params.target_url))
        return request.make_response(RefSelector(self.article_id, ref_id=rec.id).make_handle())

    def run_command_open( self, request ):
        return request.make_response(
            RefSelector(self.article_id, ref_id=request.params.element_key).make_handle())

    @db_session
    def run_element_command_delete( self, request ):
        ref_id = request.params.element_key
        module.ArticleRef[ref_id].delete()
        diff = self.Diff_delete(ref_id)
        return request.make_response_update(self.iface, self.get_path(), diff)

    @db_session
    def fetch_all_elements( self ):
        return map(self.rec2element, select(ref for ref in module.ArticleRef
            if ref.article==module.Article[self.article_id]) \
            .order_by(module.ArticleRef.id))

    def rec2element( self, rec ):
        commands = [
            Command('open', 'Open', 'Open reference selector'),
            Command('delete', 'Delete', 'Delete article reference', 'Del'),
            ]
        return self.Element(self.Row(rec.id, rec.path), commands)


class RefSelector(Object):

    iface = object_selector_iface
    objimpl_id = 'object'
    class_name = 'object_selector'

    @classmethod
    def resolve( cls, path ):
        article_id = path.pop_int()
        ref_id = path.pop_int()
        return cls(article_id, ref_id)

    def __init__( self, article_id, ref_id ):
        Object.__init__(self)
        self.article_id = article_id
        self.ref_id = ref_id

    def get_path( self ):
        return module.make_path(self.class_name, path_part_to_str(self.article_id), path_part_to_str(self.ref_id))

    def process_request( self, request ):
        if request.command_id == 'choose':
            return self.run_command_choose(request)
        return Object.process_request(self, request)

    @db_session
    def run_command_choose( self, request ):
        target_path_str = encode_url(request.params.target_url)
        if self.ref_id is None:
            rec = module.ArticleRef(article=module.Article[self.article_id],
                                    path=target_path_str)
        else:
            rec = module.ArticleRef[self.ref_id]
            rec.path = target_path_str
        commit()
        print 'Saved article#%d reference#%d path: %r' % (rec.article.id, rec.id, rec.path)
        ref_list_obj = ArticleRefList(self.article_id)
        list_elt = ArticleRefList.ListHandle(ref_list_obj.get(), rec.id)
        handle = ObjSelectorUnwrapHandle('object_selector_unwrap', list_elt)
        return request.make_response(handle)

    @db_session
    def make_handle( self ):
        if self.ref_id is None:
            target = None
        else:
            rec = module.ArticleRef[self.ref_id]
            target_url = decode_url(rec.path)
            path = target_url[1:]
            target_obj = module.run_resolver(path)
        return ObjSelectorHandle('object_selector', self.get(), target_obj.get_handle())


class ArticleModule(PonyOrmModule):

    def __init__( self ):
        PonyOrmModule.__init__(self, MODULE_NAME)
        self.article_fields = dict(text=Required(unicode),
                                   refs=Set('ArticleRef'))

    def init_phase2( self ):
        self.Article = self.make_entity('Article', **self.article_fields)
        self.ArticleRef = self.make_entity('ArticleRef',
                                           article=Required(self.Article),
                                           url=Required(str),
                                           is_local=Required(bool),
                                           )
        Article.register_class(self.Article)

    def resolve( self, path ):
        objname = path.pop_str()
        if objname == Article.class_name:
            return Article.resolve(path)
        if objname == ArticleRefList.class_name:
            return ArticleRefList.resolve(path)
        if objname == RefSelector.class_name:
            return RefSelector.resolve(path)
        path.raise_not_found()

    def get_commands( self ):
        return [ModuleCommand('create', 'Create article', 'Create new article', 'Alt+A', self.name)]

    def run_command( self, request, command_id ):
        if command_id == 'create':
            return request.make_response_handle(Article(mode=Article.mode_edit))
        return PonyOrmModule.run_command(self, request, command_id)

    def add_article_fields( self, **fields ):
        self.article_fields.update(fields)


module = ArticleModule()
