import asyncio
from typing import Awaitable

from dask.distributed import Client as DaskClient
from distributed import LocalCluster
from interfaces.task_runner import ITaskRunner


class DaskRunner(ITaskRunner):
    """
    A class to run Dask tasks in non-blocking mode.
    """

    _cluster: LocalCluster = None
    _dask_client: DaskClient = None
    _is_ready: asyncio.Event = None
    _is_initialing: bool = False

    def __init__(self):
        self._cluster = None
        self._dask_client = None
        self._is_initialing = False
        self._is_ready = asyncio.Event()
        asyncio.create_task(self._init_dask())

    async def submit(self, coro: Awaitable, *args, **kwargs):
        """
        Run a function with Dask.
        """

        if not self.is_ready():
            await self._init_dask()

        return await self._dask_client.submit(coro, *args, **kwargs)

    async def _init_dask(self):

        if self._is_initialing:
            print("Dask client is already initializing, waiting for it to finish...")
            await self._is_ready.wait()
            return

        self._is_initialing = True

        if self._cluster is None:
            self._cluster = await LocalCluster(
                asynchronous=True,
            )

        if self._dask_client is None:
            self._dask_client = await DaskClient(
                self._cluster,
                asynchronous=True,
            )

        elif self._dask_client is not None and self._dask_client.status != "running":

            print("Dask client is not running, restarting...")

            if self._cluster is not None:
                await self._cluster.close()
                self._cluster = None
                self._cluster = await LocalCluster(
                    asynchronous=True,
                )

            await self._dask_client.close()
            self._dask_client = None
            self._dask_client = await DaskClient(
                self._cluster,
                asynchronous=True,
            )

        self._is_ready.set()
        self._is_initialing = False
        print("Dask client initialization complete")

    def is_ready(self) -> bool:
        """
        Check if the task runner is ready.
        """
        if not self._dask_client:
            self._is_ready.clear()
        elif self._dask_client.status != "running":
            self._is_ready.clear()

        if not self._is_ready.is_set():
            return False

        return True

    async def close(self):
        """
        Close the aiohttp session.
        """
        if self._dask_client is not None:
            await self._dask_client.close()
            self._dask_client = None
            print("Dask client closed")

        if self._cluster is not None:
            await self._cluster.close()
            self._cluster = None
            print("Dask cluster closed")

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        """
        Close the client session when exiting the context manager.

        Example:
            async with DaskRunner() as runner:
                await runner.submit(my_function, *args)
        """
        await self.close()
