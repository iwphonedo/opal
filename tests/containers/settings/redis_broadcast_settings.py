import os

from testcontainers.core.utils import setup_logger


class RedisBroadcastSettings:
    def __init__(
        self,
        container_name: str | None = None,
        host: str | None = None,
        port: int | None = None,
        password: str | None = None,
    ):
        self.logger = setup_logger("RedisBroadcastSettings")

        self.load_from_env()

        self.container_name = container_name if container_name else self.container_name
        self.host = host if host else self.host
        self.port = port if port else self.port
        self.password = password if password else self.password
        self.protocol = "redis"

        self.validate_dependencies()

    def validate_dependencies(self):
        """Validate required dependencies before starting the server."""
        if not self.host:
            raise ValueError("REDIS_HOST is required.")
        if not self.port:
            raise ValueError("REDIS_PORT is required.")

        self.logger.info(
            f"{self.container_name} | Dependencies validated successfully."
        )

    def getEnvVars(self):
        return {
            "REDIS_HOST": self.host,
            "REDIS_PORT": self.port,
            "REDIS_PASSWORD": self.password,
        }

    def load_from_env(self):
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.password = os.getenv("REDIS_PASSWORD", None)
        self.container_name = os.getenv("REDIS_CONTAINER_NAME", "broadcast_channel")
