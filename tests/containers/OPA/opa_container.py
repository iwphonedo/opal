from testcontainers.core.generic import DockerContainer
from testcontainers.core.network import Network
from testcontainers.core.utils import setup_logger

from tests.containers.permitContainer import PermitContainer

from tests.containers.OPA.OPA_settings import OpaSettings

class OpaContainer(PermitContainer, DockerContainer):
    def __init__(
        self,
        settings: OpaSettings,
        network: Network,
        docker_client_kw: dict | None = None,
        **kwargs,
    ) -> None:
        PermitContainer.__init__(self)  # Initialize PermitContainer
        DockerContainer.__init__(
            self, image=settings.image, docker_client_kw=docker_client_kw, **kwargs
        )
        self.settings = settings
        self.network = network
        self.configure()
        self.start()

    def configure(self):
        for key, value in self.settings.getEnvVars().items():
            self.with_env(key, value)

        self.with_name(self.settings.container_name)
        self.with_bind_ports(8181, self.settings.port)
        self.with_network(self.network)
        self.with_kwargs(labels={"com.docker.compose.project": "pytest"})
        self.with_network_aliases(self.settings.container_name)
        self.with_command("run --log-level debug --server --addr :8181")

    def reload_with_settings(self, settings: OpaSettings | None = None):
        self.stop()

        self.settings = settings if settings else self.settings
        self.configure()

        self.start()
