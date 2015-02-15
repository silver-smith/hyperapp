import json
from pony.orm import db_session, Required, Optional, Set
from util import str2id
from object import Object, ListObject, Command, Element, Column
from module import ModuleCommand
from ponyorm_module import PonyOrmModule
from iface import Iface, TextObjectIface, ListIface


MODULE_NAME = 'article'


class Article(Object):

    iface = TextObjectIface()

    def __init__( self, path, article_id, mode='view' ):
        Object.__init__(self, path)
        self.article_id = article_id
        self.mode = mode
        if mode == 'edit':
            self.view_id = 'text_edit'
        else:
            self.view_id = 'text_view'

    @classmethod
    def from_path( cls, path ):
        article_id = path['article_id']
        return cls(path, article_id=article_id)

    @db_session
    def get( self, **kw ):
        if self.article_id is not None:
            rec = module.Article[self.article_id]
            text = rec.text
        else:
            text = None
        return Object.get(self, text=text, **kw)

    def get_commands( self ):
        if self.mode == 'view':
            mode_commands = [
                Command('edit', 'Edit', 'Switch to edit mode', 'E'),
                ]
        else:
            mode_commands = [
                Command('view', 'View', 'Finish editing, switch to view mode', 'Ctrl+F'),
                Command('save', 'Save', 'Save article', 'Ctrl+S'),
                ]
        return mode_commands + [
            Command('refs', 'Refs', 'Open article references', 'Ctrl+R'),
            ]

    def run_command( self, request, command_id ):
        if command_id == 'view':
            return request.make_response_object(Article(self.path, self.article_id, mode='view'))
        if command_id == 'edit':
            return request.make_response_object(Article(self.path, self.article_id, mode='edit'))
        if command_id == 'save':
            return self.run_command_save(request)
        elif command_id == 'refs':
            return self.run_command_refs(request)
        elif command_id == 'open_ref':
            return self.run_command_open_ref(request)
        else:
            return Object.run_command(self, request, command_id)

    def run_command_save( self, request ):
        text = request['text']
        new_path = self.do_save(text)
        return request.make_response_result(new_path=new_path)

    def run_command_refs( self, request ):
        return request.make_response_object(ArticleRefList.make(self.article_id))

    @db_session
    def run_command_open_ref( self, request ):
        ref_id = request['ref_id']
        rec = module.ArticleRef[ref_id]
        target_path = json.loads(rec.path)
        target = module.run_resolve(target_path)
        return request.make_response_object(target)

    def do_save( self, text ):
        with db_session:
            if self.article_id is not None:
                article_rec = module.Article[self.article_id]
            else:
                article_rec = None
            article_rec = self.save_article(article_rec, text)
        print 'Article is saved, article_id =', article_rec.id
        return dict(self.path, article_id=article_rec.id)

    def save_article( self, article_rec, text ):
        if article_rec is not None:
            article_rec.text = text
        else:
            article_rec = module.Article(text=text)
        return article_rec


class ArticleRefList(ListObject):

    iface = ListIface('ref_list')
    view_id = 'list'

    columns = [
        Column('key', 'Ref id'),
        Column('path', 'Path'),
        ]

    def __init__( self, path, article_id ):
        ListObject.__init__(self, path)
        self.article_id = article_id

    @classmethod
    def make( cls, article_id ):
        path = module.make_path(object='article_ref_list', article_id=article_id)
        return cls(path, article_id)

    @classmethod
    def from_path( cls, path ):
        article_id = path['article_id']
        return cls(path, article_id)

    def get_commands( self ):
        return [Command('add', 'Add ref', 'Create new reference', 'Ins')]

    def run_command( self, request, command_id ):
        if command_id == 'add':
            return self.run_command_add(request)
        assert False, repr(command_id)  # Unsupported command

    def run_command_add( self, request ):
        target_path = request['target_path']
        with db_session:
            rec = module.ArticleRef(article=module.Article[self.article_id],
                                    path=json.dumps(target_path))
        return request.make_response_object(RefSelector.make(self.article_id, ref_id=rec.id))

    @db_session
    def get_all_elements( self ):
        return map(self.rec2element, module.Article[self.article_id].refs)

    def rec2element( self, rec ):
        commands = [
            Command('open', 'Open', 'Open reference selector'),
            Command('delete', 'Delete', 'Delete article reference', 'Del'),
            ]
        return Element(rec.id, [rec.id, rec.path], commands)

    def run_element_command( self, request, command_id, element_key ):
        if command_id == 'open':
            return request.make_response_object(RefSelector.make(self.article_id, ref_id=element_key))
        if command_id == 'delete':
            return self.run_element_command_delete(request, element_key)
        return ListObject.run_element_command(self, request, command_id, element_key)

    @db_session
    def run_element_command_delete( self, request, ref_id ):
        module.ArticleRef[ref_id].delete()
        return request.make_response_object(self)  # reload


class RefSelector(Object):

    iface = Iface('object_selector')
    view_id = 'object_selector'

    def __init__( self, path, article_id, ref_id ):
        Object.__init__(self, path)
        self.article_id = article_id
        self.ref_id = ref_id

    @classmethod
    def make( cls, article_id, ref_id ):
        path = module.make_path(object='article_ref_selector', article_id=article_id, ref_id=ref_id)
        return cls(path, article_id, ref_id)

    @classmethod
    def from_path( cls, path ):
        article_id = path['article_id']
        ref_id = path['ref_id']
        return cls(path, article_id, ref_id)

    @db_session
    def get( self, **kw ):
        if self.ref_id is None:
            target = None
        else:
            rec = module.ArticleRef[self.ref_id]
            target_path = json.loads(rec.path)
            target = module.run_resolve(target_path)
        return Object.get(self, target=target.get() if target else None, **kw)

    def run_command( self, request, command_id ):
        if command_id == 'choose':
            return self.run_command_choose(request)
        return Object.run_command(self, request, command_id)

    def run_command_choose( self, request ):
        target_path = request['target_path']
        target_path_str = json.dumps(target_path)
        with db_session:
            if self.ref_id is None:
                rec = module.ArticleRef(article=module.Article[self.article_id],
                                        path=target_path_str)
            else:
                rec = module.ArticleRef[self.ref_id]
                rec.path = target_path_str
        print 'Saved article#%d reference#%d path: %r' % (rec.article.id, rec.id, rec.path)
        return request.make_response_object(ArticleRefList.make(article_id=self.article_id))


class ArticleModule(PonyOrmModule):

    def __init__( self ):
        PonyOrmModule.__init__(self, MODULE_NAME)
        self.article_fields = dict(text=Required(unicode),
                                   refs=Set('ArticleRef'))

    def init_phase2( self ):
        self.Article = self.make_entity('Article', **self.article_fields)
        self.ArticleRef = self.make_entity('ArticleRef',
                                           article=Required(self.Article),
                                           path=Optional(str),
                                           )

    def resolve( self, path ):
        objname = path.get('object')
        if objname == 'article':
            return Article.from_path(path)
        if objname == 'article_ref_list':
            return ArticleRefList.from_path(path)
        if objname == 'article_ref_selector':
            return RefSelector.from_path(path)
        assert objname is None, repr(objname)  # Unknown object name
        return PonyOrmModule.resolve(self, path)

    def get_commands( self ):
        return [ModuleCommand('create', 'Create article', 'Create new article', 'Alt+A', self.name)]

    def run_command( self, request, command_id ):
        if command_id == 'create':
            return request.make_response_object(Article.from_path(self.make_path(object='article', article_id=None)))
        return PonyOrmModule.run_command(self, request, command_id)

    def add_article_fields( self, **fields ):
        self.article_fields.update(fields)


module = ArticleModule()
