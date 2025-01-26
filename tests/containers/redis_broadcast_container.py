from testcontainers.core.network import Network
from testcontainers.redis import RedisContainer

from tests.containers.broadcast_container_base import BroadcastContainerBase
from tests.containers.settings.redis_broadcast_settings import RedisBroadcastSettings
from tests.containers.permitContainer import PermitContainer


class RedisBroadcastContainer(PermitContainer, RedisContainer):
    def __init__(
        self,
        network: Network,
        redisContainerSettings: RedisBroadcastSettings,
        docker_client_kw: dict | None = None,
        **kwargs,
    ) -> None:

        self.settings = redisContainerSettings

        self.network = network

        PermitContainer.__init__(self)
        RedisContainer.__init__(self, docker_client_kw=docker_client_kw, **kwargs)

        self.with_network(self.network)

        self.with_network_aliases("broadcast_channel")
        # Add a custom name for the container
        self.with_name(self.settings.container_name)

        self.start()
