import debugpy
from testcontainers.core.network import Network
from testcontainers.kafka import KafkaContainer

from tests.containers.broadcast_container_base import BroadcastContainerBase
from tests.containers.PermitContainer import PermitContainer
from tests.containers.settings import kafka_broadcast_settings
from tests.containers.zookeeper_container import ZookeeperContainer


class KafkaBroadcastContainer(PermitContainer, KafkaContainer):
    def __init__(
        self,
        network: Network,
        zookeeper_container: ZookeeperContainer,
        kafka_settings: kafka_broadcast_settings,
        docker_client_kw: dict | None = None,
        **kwargs,
    ) -> None:
        # Add custom labels to the kwargs
        labels = kwargs.get("labels", {})
        labels.update({"com.docker.compose.project": "pytest"})
        kwargs["labels"] = labels

        self.settings = kafka_settings

        self.zookeeper_container = zookeeper_container
        self.network = network

        PermitContainer.__init__(self)
        KafkaContainer.__init__(self, docker_client_kw=docker_client_kw, **kwargs)

        self.with_network(self.network)

        for key, value in self.settings.getKafkaEnvVars().items():
            self.with_env(key, value)

        self.with_network_aliases("broadcast_channel")

        # Add a custom name for the container
        self.with_name(self.settings.kafka_container_name)

        self.start()
