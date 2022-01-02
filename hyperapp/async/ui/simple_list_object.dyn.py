import abc

from .list_object import ListObject


class SimpleListObject(ListObject):

    @abc.abstractmethod
    async def get_all_items(self):
        pass

    async def fetch_items(self, from_key, fetcher):
        items = await self.get_all_items()
        if from_key is not None:
            key_attr = self.key_attribute
            idx = 0
            while idx < len(items):
                if getattr(items[idx], key_attr) == from_key:
                    items = items[idx + 1:]
                    break
                idx += 1
            else:
                assert f"{from_key!r} is not present in any of {items}"
        fetcher.process_fetch_results(items, fetch_finished=True)
        fetcher.process_eof()
