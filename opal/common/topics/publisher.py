import asyncio
from typing import Any, List
from fastapi_websocket_pubsub import PubSubClient, TopicList

from opal.common.logger import get_logger


logger = get_logger("opal.common.topics.publisher")


class TopicPublisher:
    """
    A simple wrapper around a PubSubClient that exposes publish().
    Provides start() and stop() shortcuts that helps treat this client
    as a separate "process" or task that runs in the background.
    """
    def __init__(self, client: PubSubClient, server_uri: str):
        """[summary]

        Args:
            client (PubSubClient): a configured not-yet-started pub sub client
            server_uri (str): the URI of the pub sub server we publish to
        """
        self._client = client
        self._server_uri = server_uri
        self._tasks: List[asyncio.Task] = []

    async def __aenter__(self):
        self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.stop()

    def start(self):
        """
        starts the pub/sub client as a background asyncio task.
        the client will attempt to connect to the pubsub server until successful.
        """
        logger.info("started topic publisher")
        self._client.start_client(f"{self._server_uri}")

    async def stop(self):
        """
        stops the pubsub client, and cancels any publishing tasks.
        """
        await self._client.disconnect()
        for task in self._tasks:
            if not task.done():
                task.cancel()
        try:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        except asyncio.CancelledError:
            pass
        logger.info("stopped topic publisher")

    async def wait_until_done(self):
        """
        When the publisher is a used as a context manager, this method waits until
        the client is done (i.e: terminated) to prevent exiting the context.
        """
        return await self._client.wait_until_done()

    def publish(self, topics: TopicList, data: Any = None):
        """
        publish a message by launching a background task on the event loop.

        Args:
            topics (TopicList): a list of topics to publish the message to
            data (Any): optional data to publish as part of the message
        """
        self._tasks.append(asyncio.create_task(self._publish(topics=topics, data=data)))

    async def _publish(self, topics: TopicList, data: Any = None) -> bool:
        """
        Do not trigger directly, must be triggered via publish()
        in order to run as a monitored background asyncio task.
        """
        await self._client.wait_until_ready()
        return await self._client.publish(topics, data)