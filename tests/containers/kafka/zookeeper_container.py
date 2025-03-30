from testcontainers.core.container import DockerContainer
from testcontainers.core.network import Network

class ZookeeperContainer(DockerContainer):
    def __init__(self, network: Network):
        
        self.settings = {
            "env": {
                "ZOOKEEPER_CLIENT_PORT": "2181",
                "ZOOKEEPER_TICK_TIME": "2000",
                "ALLOW_ANONYMOUS_LOGIN": "yes",
            }
        }

        DockerContainer.__init__(self, image="confluentinc/cp-zookeeper:6.2.0")
        self.with_exposed_ports(2181)
        
        self.with_name("zookeeper")
        for key, value in self.settings.get("env").items():
            self.with_env(key, value)
        self.with_network(network)
        self.with_network_aliases("zookeeper")

        self.start()
