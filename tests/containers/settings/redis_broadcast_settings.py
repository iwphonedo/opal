import os

from testcontainers.core.utils import setup_logger


class RedisBroadcastSettings:
    def __init__(
        self,
        container_name: str | None = None,
        port: int | None = None,
        password: str | None = None,
    ):
        self.logger = setup_logger("PostgresBroadcastSettings")

        self.load_from_env()

        self.container_name = container_name if container_name else self.container_name
        self.port = port if port else self.port
        self.password = password if password else self.password
        self.protocol = "redis"

        self.validate_dependencies()

    def validate_dependencies(self):
        """Validate required dependencies before starting the server."""
        if not self.port:
            raise ValueError("POSTGRES_PORT is required.")
        if not self.password:
            raise ValueError("POSTGRES_PASSWORD is required.")

        self.logger.info(
            f"{self.container_name} | Dependencies validated successfully."
        )

    def load_from_env(self):
        self.container_name = os.getenv(
            "REDIS_CONTAINER_NAME", "redis_broadcast_channel"
        )
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.password = os.getenv("REDIS_PASSWORD", "redis")
