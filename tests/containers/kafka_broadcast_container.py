import debugpy
from testcontainers.core.network import Network
from testcontainers.kafka import KafkaContainer

import docker
from tests.containers.broadcast_container_base import BroadcastContainerBase
from tests.containers.settings.kafka_broadcast_settings import KafkaBroadcastSettings
from tests.containers.zookeeper_container import ZookeeperContainer


class KafkaBroadcastContainer(BroadcastContainerBase, KafkaContainer):
    def __init__(
        self,
        network: Network,
        settings: KafkaBroadcastSettings,
        zookeeper_container: ZookeeperContainer,
        docker_client_kw: dict | None = None,
        **kwargs,
    ) -> None:
        self.zookeeper_container = zookeeper_container
        self.network = network

        self.settings = settings

        BroadcastContainerBase.__init__(self)
        KafkaContainer.__init__(self, docker_client_kw=docker_client_kw, **kwargs)

        self.with_network(self.network)

        self.with_network_aliases("broadcast_channel")
        self.with_name(f"kafka_broadcast_channel")

    def get_url(self) -> str:
        url = (
            self.settings.protocol
            + "://"
            + self.settings.kafka_container_name
            + ":"
            + str(self.settings.kafka_port)
        )
        print(url)
        return url
