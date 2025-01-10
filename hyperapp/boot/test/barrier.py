import asyncio


class Barrier:

    def __init__(self, parties):
        self._wanted_entries = parties
        self._cond = asyncio.Condition()

    async def wait(self):
        async with self._cond:
            self._wanted_entries -= 1
            await self._cond.wait_for(lambda: self._wanted_entries == 0)
            self._cond.notify_all()
