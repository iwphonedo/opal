from tests import utils
from tests.containers.settings.opal_client_settings import OpalClientSettings


class OpaSettings:
    def __init__(
        self,
        image: str | None = None,
        port: int | None = None,
        container_name: str | None = None,
    ) -> None:
        self.image = image if image else "openpolicyagent/opa:0.29.0"
        self.container_name = "opa"

        if port is None:
            self.port = utils.find_available_port(8181)
        else:
            if utils.is_port_available(port):
                self.port = port
            else:
                self.port = utils.find_available_port(8181)

    def getEnvVars(self):
        return {}
