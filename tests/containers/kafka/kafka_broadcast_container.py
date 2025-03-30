from testcontainers.core.container import DockerContainer
from testcontainers.core.network import Network


class KafkaContainer(DockerContainer):
    def __init__(self, network: Network):
        # Kafka Broker 0
        self.settings = {
            "env": {
                "KAFKA_BROKER_ID": "1",
                "KAFKA_ZOOKEEPER_CONNECT": "zookeeper:2181",
                "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR": "1",
                "KAFKA_LISTENER_SECURITY_PROTOCOL_MAP": "PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT",
                "KAFKA_ADVERTISED_LISTENERS": "PLAINTEXT_HOST://localhost:29092,PLAINTEXT://kafka0:9092",
                "ALLOW_PLAINTEXT_LISTENER": "yes",
                "KAFKA_TOPIC_AUTO_CREATE": "true",
                "KAFKA_TRANSACTION_STATE_LOG_MIN_ISR": "1",
                "KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR": "1",
            }
        }
        DockerContainer.__init__(self, image="confluentinc/cp-kafka:6.2.0")
        self.with_exposed_ports(9092, 29092)
        for key, value in self.settings.get("env").items():
            self.with_env(key, value)

        self.with_name("kafka0")
        self.with_network(network)
        self.with_network_aliases("kafka0")

        self.start()

    def get_url(self) -> str:
        url = "kafka://kafka0:9092"
        return url
