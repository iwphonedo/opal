from testcontainers.core.container import DockerContainer
from testcontainers.core.network import Network

from tests.containers.kafka_broadcast_container import KafkaBroadcastContainer
from tests.containers.opal_test_container import OpalTestContainer
from tests.containers.settings.kafka_broadcast_settings import KafkaBroadcastSettings


class KafkaUIContainer(OpalTestContainer, DockerContainer):
    def __init__(
        self,
        network: Network,
        settings: KafkaBroadcastSettings,
        kafka_container: KafkaBroadcastContainer,
        docker_client_kw: dict | None = None,
        **kwargs,
    ) -> None:
        self.network = network
        self.settings = settings
        self.kafka_container = kafka_container

        self.image = "provectuslabs/kafka-ui:latest"

        OpalTestContainer.__init__(self)
        DockerContainer.__init__(
            self, image=self.image, docker_client_kw=docker_client_kw, **kwargs
        )

        self.with_name("kafka-ui")
        self.with_bind_ports(8080, 8080)
        self.with_env("KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS", "kafka:9092")

        self.with_network(self.network)
        self.with_network_aliases("Kafka_ui")
