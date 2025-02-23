from testcontainers.core.container import DockerContainer
from testcontainers.core.network import Network


class KafkaUIContainer(DockerContainer):
    def __init__(self, network: Network):
        self.settings = {
            "env": {
                "KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS": "kafka0:9092",
            }
        }
        DockerContainer.__init__(self, image="provectuslabs/kafka-ui:latest")
        self.with_exposed_ports(8080)
        for key, value in self.settings.get("env").items():
            self.with_env(key, value)
        self.with_name("kafka-ui")
        self.with_network(network)
        self.with_network_aliases("kafka-ui")

        self.start()
     