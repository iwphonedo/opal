from testcontainers.core.network import Network
from testcontainers.redis import RedisContainer

from tests.containers.broadcast_container_base import BroadcastContainerBase
from tests.containers.settings.redis_broadcast_settings import RedisBroadcastSettings


class RedisBroadcastContainer(BroadcastContainerBase, RedisContainer):
    def __init__(
        self,
        network: Network,
        settings: RedisBroadcastSettings,
        docker_client_kw: dict | None = None,
        **kwargs,
    ) -> None:
        self.network = network
        self.settings = settings

        BroadcastContainerBase.__init__(self)
        RedisContainer.__init__(self, docker_client_kw=docker_client_kw, **kwargs)

        self.with_network(self.network)

        self.with_network_aliases("broadcast_channel")
        self.with_name(f"redis_broadcast_channel")

        self.start()

    def get_url(self) -> str:
        password_str = ""
        if self.settings.password:
            password_str = f":{self.settings.password}@"

        url = (
            self.settings.protocol
            + "://"
            # + self.settings.user
            + password_str
            + self.settings.container_name
            + ":"
            + str(self.settings.port)
        )
        print(url)
        return url
