from testcontainers.core.container import DockerContainer
from testcontainers.core.network import Network
from testcontainers.redis import RedisContainer

from tests import utils
from tests.containers.permitContainer import PermitContainer



class RedisUIContainer(PermitContainer, DockerContainer):
    def __init__(
        self,
        network: Network,
        redis_container: RedisContainer,
        docker_client_kw: dict | None = None,
        **kwargs,
    ) -> None:

        self.redis_container = redis_container
        self.network = network
        self.container_name = f"{self.redis_container.settings.container_name}-ui"
        self.image = "redis/redisinsight:latest"

        PermitContainer.__init__(self)
        DockerContainer.__init__(
            self, image=self.image, docker_client_kw=docker_client_kw, **kwargs
        )

        self.with_name(self.container_name)

        self.with_network(self.network)
        self.with_bind_ports(5540, utils.find_available_port(5540))

        self.with_network_aliases("redis_ui")

        self.start()