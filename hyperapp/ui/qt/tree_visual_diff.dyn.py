from collections import namedtuple


VisualTreeDiffAppend = namedtuple('VisualTreeDiffAppend', 'parent_id')
VisualTreeDiffInsert = namedtuple('VisualTreeDiffInsert', 'parent_id idx')
VisualTreeDiffReplace = namedtuple('VisualTreeDiffReplace', 'parent_id idx')
VisualTreeDiffRemove = namedtuple('VisualTreeDiffRemove', 'parent_id idx')
