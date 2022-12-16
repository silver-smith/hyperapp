from . import htypes
from .code.marker import param


param.SampleList.piece = htypes.sample_list.sample_list(provider='fixture')
param.SampleList.open.current_key = 123
