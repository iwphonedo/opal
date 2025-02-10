import debugpy
from testcontainers.core.container import DockerContainer
from testcontainers.core.network import Network

import docker
from tests.containers.opal_test_container import OpalTestContainer
from tests.containers.settings.kafka_broadcast_settings import KafkaBroadcastSettings


class ZookeeperContainer(OpalTestContainer, DockerContainer):
    def __init__(
        self,
        network: Network,
        settings: KafkaBroadcastSettings,
        docker_client_kw: dict | None = None,
        **kwargs,
    ) -> None:
        self.network = network

        self.settings = settings

        OpalTestContainer.__init__(self)
        DockerContainer.__init__(
            self,
            image="confluentinc/cp-zookeeper:latest",
            docker_client_kw=docker_client_kw,
            **kwargs,
        )

        self.with_bind_ports(self.settings.zookeeper_port, self.settings.zookeeper_port)
        self.with_env("ZOOKEEPER_CLIENT_PORT", self.settings.zookeeper_port)
        self.with_env("ZOOKEEPER_TICK_TIME", self.settings.zookeeper_tick_time)
        self.with_env(
            "ALLOW_ANONYMOUS_LOGIN", self.settings.zookeeper_allow_anonymous_login
        )

        self.with_network(self.network)

        self.with_network_aliases("zookeper")
        self.with_name(f"zookeeper")
