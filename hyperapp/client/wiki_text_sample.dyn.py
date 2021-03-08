from . import htypes
from .object_command import command
from .module import ClientModule


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services)
        ref_list = [
            htypes.text.wiki_ref(1, "Sample ref#1", services.mosaic.put(htypes.text.text("Referred text 1"))),
            htypes.text.wiki_ref(2, "Sample ref#2", services.mosaic.put(htypes.text.text("Referred text 2"))),
            ]
        self._wiki_text = htypes.text.wiki_text(
            "Sample wiki text\n"
            "This is ref#[1].\n"
            "And this is ref#[2].",
            ref_list)

    @command('open_wiki_sample')
    async def open_wiki_sample(self):
        return self._wiki_text
