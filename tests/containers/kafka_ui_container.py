from testcontainers.core.container import DockerContainer
from testcontainers.core.network import Network

from tests.containers.kafka_broadcast_container import KafkaBroadcastContainer
from tests.containers.PermitContainer import PermitContainer
from tests.containers.settings.kafka_broadcast_settings import KafkaBroadcastSettings


class KafkaUIContainer(PermitContainer, DockerContainer):
    def __init__(
        self,
        network: Network,
        kafka_container: KafkaBroadcastContainer,
        kafka_settings: KafkaBroadcastSettings,
        docker_client_kw: dict | None = None,
        **kwargs,
    ) -> None:
        # Add custom labels to the kwargs
        labels = kwargs.get("labels", {})
        labels.update({"com.docker.compose.project": "pytest"})
        kwargs["labels"] = labels

        self.settings = kafka_settings

        self.kafka_container = kafka_container
        self.network = network

        self.image = "provectuslabs/kafka-ui:latest"

        PermitContainer.__init__(self)
        DockerContainer.__init__(
            self, image=self.image, docker_client_kw=docker_client_kw, **kwargs
        )


        for key, value in self.settings.getKafkaUiEnvVars().items():
            self.with_env(key, value)

        self.with_bind_ports(8080, self.settings.kafka_ui_port)
        self.with_name(self.settings.kafka_ui_container_name)

        self.with_network(self.network)
        self.with_network_aliases("Kafka_ui")

        self.start()