from testcontainers.core.container import DockerContainer
import pytest
from testcontainers.core.network import Network
from testcontainers.core.utils import setup_logger

from tests.containers.kafka_broadcast_container import KafkaBroadcastContainer
from tests.containers.kafka_ui_container import KafkaUIContainer
from tests.containers.postgres_broadcast_container import PostgresBroadcastContainer
from tests.containers.redis_broadcast_container import RedisBroadcastContainer
from tests.containers.redis_ui_container import RedisUIContainer
from tests.containers.settings.kafka_broadcast_settings import KafkaBroadcastSettings
from tests.containers.settings.postgres_broadcast_settings import (
    PostgresBroadcastSettings,
)
from tests.containers.settings.redis_broadcast_settings import RedisBroadcastSettings
from tests.containers.zookeeper_container import ZookeeperContainer

logger = setup_logger(__name__)


@pytest.fixture(scope="session")
def postgres_broadcast_channel(opal_network: Network):
    """Fixture that yields a running Postgres broadcast channel container.

    The container is started once and kept running throughout the entire
    test session. It is stopped once all tests have finished running,
    unless an exception is raised during teardown.
    """
    try:
        container = PostgresBroadcastContainer(
            network=opal_network, settings=PostgresBroadcastSettings()
        )
        yield container

        try:
            if container.get_wrapped_container().status == "running":
                container.stop()
        except Exception:
            logger.error(
                f"Failed to stop containers: {container.settings.container_name}"
            )
            return

    except Exception as e:
        logger.error(
            f"Failed on container: {container.settings.container_name} with error: {e} {e.__traceback__}"
        )
        return

@pytest.fixture(scope="session")
def kafka_broadcast_channel(opal_network: Network):
    """Fixture that sets up a Kafka broadcast channel for testing purposes.
    
    This fixture initializes all necessary Kafka-related containers, connecting them to the specified network.
    It yields a list of these containers, which remain running throughout the test session. At the end of the session,
    it attempts to stop each container, logging an error if any container fails to stop.
    """
    
    from tests.containers.kafka.Kafka_ui import KafkaUIContainer
    from tests.containers.kafka.KafkaContainer import KafkaContainer
    from tests.containers.kafka.Zookeeper import ZookeeperContainer
    import time

    zookeeper = ZookeeperContainer(opal_network)
    # zookeeper.start()
    time.sleep(5)
    
    kafka0 = KafkaContainer(opal_network)
    # kafka0.start()
    time.sleep(5)
    
    kafka_ui = KafkaUIContainer(opal_network)
    # kafka_ui.start()
    time.sleep(5)

    yield [kafka0, zookeeper, kafka_ui]

    zookeeper.stop()
    kafka0.stop()
    kafka_ui.stop()



@pytest.fixture(scope="session")
def redis_broadcast_channel(opal_network: Network):
    """Fixture that yields a running redis broadcast channel container.

    The fixture starts a redis broadcast container and a redis ui
    container. The yield value is a list of the two containers. The
    fixture stops the containers after the test is done.
    """
    redis_container = RedisBroadcastContainer(opal_network, RedisBroadcastSettings())
    redis_ui_container = RedisUIContainer(opal_network, redis_container)

    containers = [redis_container, redis_ui_container]
    yield containers

    for container in containers:
        try:
            container.stop()
        except Exception:
            logger.error(f"Failed to stop containers: {container}")
            return


@pytest.fixture(scope="session")
def broadcast_channel(opal_network: Network, postgres_broadcast_channel):
    """Fixture that yields a running broadcast channel container.

    The container is started once and kept running throughout the entire
    test session. It is stopped once all tests have finished running,
    unless an exception is raised during teardown.
    """

    yield postgres_broadcast_channel

    try:
        postgres_broadcast_channel.stop()
    except Exception:
        logger.error(f"Failed to stop containers: {postgres_broadcast_channel}")
        return
