import json
import os
import shutil
import tempfile
import threading
import time
from typing import List

import debugpy
import pytest
from testcontainers.core.network import Network
from testcontainers.core.utils import setup_logger

from tests import utils
from tests.containers.broadcast_container_base import BroadcastContainerBase
from tests.containers.opal_client_container import OpalClientContainer
from tests.containers.opal_server_container import OpalServerContainer
from tests.containers.settings.opal_client_settings import OpalClientSettings
from tests.containers.settings.opal_server_settings import OpalServerSettings
from tests.policy_repos.policy_repo_base import PolicyRepoBase
from tests.settings import pytest_settings

logger = setup_logger(__name__)

# wait some seconds for the debugger to attach
debugger_wait_time = 5  # seconds


def cancel_wait_for_client_after_timeout():
    try:
        time.sleep(debugger_wait_time)
        debugpy.wait_for_client.cancel()
    except Exception as e:
        logger.debug(f"Failed to cancel wait for client: {e}")


try:
    if pytest_settings.wait_for_debugger:
        t = threading.Thread(target=cancel_wait_for_client_after_timeout)
        t.start()
        logger.debug(f"Waiting for debugger to attach... {debugger_wait_time} seconds timeout")
        debugpy.wait_for_client()
except Exception as e:
    logger.debug(f"Failed to attach debugger: {e}")

utils.export_env("OPAL_TESTS_DEBUG", "true")
# utils.install_opal_server_and_client()


@pytest.fixture(scope="session")
def temp_dir():
    # Setup: Create a temporary directory
    """Creates a temporary directory once at the beginning of the test session,
    prints the directory path to the console, and yields it to the test.

    After the test session is finished, it deletes the directory and
    prints the directory removal to the console.

    This fixture is useful for tests that need a temporary directory to
    exist for the duration of the test session.
    """
    from pathlib import Path

    path = Path("~/opal.tmp").expanduser()
    path.mkdir(parents=True, exist_ok=True)
    os.chmod(path, 0o777)  # Set permissions to allow read/write/execute for all users

    dir_path = tempfile.mkdtemp(prefix="opal_tests_",suffix=".tmp",dir=str(path))
    os.chmod(dir_path, 0o777)  # Set permissions to allow read/write/execute for all users
    logger.debug(f"Temporary directory created: {dir_path}")
    yield dir_path

    # Teardown: Clean up the temporary directory
    shutil.rmtree(dir_path)
    shutil.rmtree(path)
    logger.debug(f"Temporary directory removed: {dir_path}")


@pytest.fixture(scope="session", autouse=True)
def opal_network():
    """Creates a Docker network and yields it.

    The network is cleaned up after all tests have finished running.
    """
    network = Network().create()

    yield network

    logger.info("Removing network...")
    time.sleep(3)  # wait for the containers to stop
    try:
        network.remove()
        logger.info("Network removed.")
    except Exception as e:
        if logger.level == "DEBUG":
            logger.error(f"Failed to remove network: {e}")
        else:
            logger.error(f"Failed to remove network got exception\n{e}")

from tests.fixtures.broadcasters import (
    broadcast_channel,
    kafka_broadcast_channel,
    postgres_broadcast_channel,
    redis_broadcast_channel,
)
from tests.fixtures.images import opal_server_image
from tests.fixtures.policy_repos import policy_repo


@pytest.fixture(scope="session")
def opal_servers(
    opal_network: Network,
    policy_repo,
    opal_server_image: str,
    broadcast_channel: BroadcastContainerBase,
    # kafka_broadcast_channel: KafkaContainer,
    # redis_broadcast_channel: RedisBroadcastContainer,
    session_matrix,
):
    """Fixture that initializes and manages OPAL server containers for testing.

    This fixture sets up a specified number of OPAL server containers, each
    connected to the provided Docker network and using the specified broadcast
    channel. The first server container sets up and creates a webhook for the
    policy repository. All containers are started and their logs are monitored
    for successful cloning of the policy repository. The containers are stopped
    after the test session is complete.

    Args:
        opal_network (Network): The Docker network to which the containers are connected.
        broadcast_channel (BroadcastContainerBase): The broadcast channel container.
        policy_repo (PolicyRepoBase): The policy repository to be used.
        number_of_opal_servers (int): The number of OPAL server containers to start.
        opal_server_image (str): The Docker image used for the OPAL servers.
        topics (dict[str, int]): The topics for OPAL data configuration.
        kafka_broadcast_channel (KafkaBroadcastContainer): The Kafka broadcast channel container.
        redis_broadcast_channel (RedisBroadcastContainer): The Redis broadcast channel container.
        session_matrix: The session matrix used for the test configuration.

    Yields:
        List[OpalServerContainer]: A list of running OPAL server containers.
    """

    # broadcast_channel = redis_broadcast_channel
    # broadcast_channel = kafka_broadcast_channel
    broadcast_channel = broadcast_channel[0]

    if not broadcast_channel:
        raise ValueError("Missing 'broadcast_channel' container.")

    containers = []  # List to store container instances


    for i in range(session_matrix["number_of_opal_servers"]):
        container_name = f"opal_server_{i+1}"

        repo_url = policy_repo.get_repo_url()
        container = OpalServerContainer(
            OpalServerSettings(
                broadcast_uri=broadcast_channel.get_url(),
                container_name=container_name,
                container_index=i + 1,
                uvicorn_workers="4",
                policy_repo_url=repo_url,
                image=opal_server_image,
                log_level="DEBUG",
                data_topics=" ".join(session_matrix["topics"].keys()),
                polling_interval=3,
                policy_repo_main_branch=policy_repo.test_branch,
            ),
            network=opal_network,
        )

        container.start()
        container.get_wrapped_container().reload()

        if i == 0:
            # Only the first server should setup the webhook
            # policy_repo.setup_webhook(
            #     container.get_container_host_ip(), container.settings.port
            # )
            # policy_repo.create_webhook()
            pass

        logger.info(
            f"Started container: {container_name}, ID: {container.get_wrapped_container().id}"
        )
        container.wait_for_log("Clone succeeded", timeout=30)
        containers.append(container)

    yield containers

    for container in containers:
        container.stop()

@pytest.fixture(scope="session")
def connected_clients(opal_clients: List[OpalClientContainer]):
    """A fixture that waits for all OPAL clients to connect to the PubSub
    server before yielding them.

    This fixture takes a list of OPAL clients as input and waits for each of them
    to connect to the PubSub server before yielding them. The fixture is used to
    ensure that all OPAL clients are connected and ready to receive messages
    before the tests are executed.

    Parameters
    ----------
    opal_clients : List[OpalClientContainer]
        A list of OPAL client containers.

    Yields
    ------
    List[OpalClientContainer]
        A list of connected OPAL client containers.
    """
    for client in opal_clients:
        assert client.wait_for_log(
            log_str="Connected to PubSub server", timeout=30
        ), f"Client {client.settings.container_name} did not connect to PubSub server."
    yield opal_clients


from tests.fixtures.images import (
    cedar_image,
    opa_image,
    opal_client_image,
    opal_client_with_opa_image,
)
from tests.fixtures.policy_stores import cedar_server, opa_server


@pytest.fixture(scope="session")
def opal_clients(
    opal_network: Network,
    opal_servers: List[OpalServerContainer],
    # opa_server: OpaContainer,
    # cedar_server: CedarContainer,
    request,
    session_matrix,
    opal_client_with_opa_image,
):
    """A fixture that starts and manages multiple OPAL client containers.

    This fixture takes a list of OPAL server containers as input and starts a
    specified number of OPAL client containers, each connected to the first
    OPAL server container. The fixture yields the list of started OPAL client
    containers.

    Parameters
    ----------
    opal_network : Network
        The Docker network to which the containers are connected.
    opal_servers : List[OpalServerContainer]
        A list of OPAL server containers.
    #opa_server : OpaContainer
        # The OPA server container.
    cedar_server : CedarContainer
        The Cedar server container.
    request
        The pytest request object.
    number_of_opal_clients : int
        The number of OPAL clients to start.
    opal_client_image
        The Docker image used for the OPAL clients.

    Yields
    ------
    List[OpalClientContainer]
        A list of started OPAL client containers.
    """
    if not opal_servers or len(opal_servers) == 0:
        raise ValueError("Missing 'opal_server' container.")

    opal_server_url = f"http://{opal_servers[0].settings.container_name}:7002"#{opal_servers[0].settings.port}"

    containers = []  # List to store OpalClientContainer instances

    for i in range(session_matrix["number_of_opal_clients"]):
        container_name = f"opal_client_{i+1}"  # Unique name for each client

        client_token = opal_servers[0].obtain_OPAL_tokens(container_name)["client"]
        callbacks = json.dumps(
            {
                "callbacks": [
                    [
                        f"{opal_server_url}/data/callback_report",
                        {
                            "method": "post",
                            "process_data": False,
                            "headers": {
                                "Authorization": f"Bearer {client_token}",
                                "content-type": "application/json",
                            },
                        },
                    ]
                ]
            }
        )

        container = OpalClientContainer(
            OpalClientSettings(
                image=opal_client_with_opa_image,
                container_name=container_name,
                container_index=i + 1,
                opal_server_url=opal_server_url,
                client_token=client_token,
                default_update_callbacks=callbacks,
                # inline_opa_enabled=False,
                # policy_store_url=f"http://localhost:8181",#{opa_server.settings.port}",
                # opa_port=opa_server.settings.port,
            ),
            network=opal_network,
        )

        container.start()
        logger.info(
            f"Started OpalClientContainer: {container_name}, ID: {container.get_wrapped_container().id}"
        )
        containers.append(container)

    yield containers

    try:
        for container in containers:
            container.stop()
    except Exception:
        logger.error(f"Failed to stop containers: {container}")
        pass

@pytest.fixture(scope="session")
def topiced_clients(opal_network: Network, opal_servers: list[OpalServerContainer], session_matrix):
    """Fixture that starts and manages multiple OPAL client containers, each
    subscribing to a different topic.

    The fixture takes a dictionary of topics and the number of clients to
    subscribe to each topic. It starts the specified number of OPAL client
    containers, each connected to the first OPAL server container, and each
    subscribing to the specified topic. The fixture yields the list of started
    OPAL client containers, organized by topic.

    Parameters
    ----------
    topics : dict
        A dictionary mapping topic names to the number of OpalClientContainer
        instances that should subscribe to each topic.
    opal_network : Network
        The Docker network to which the containers are connected.
    opal_servers : list[OpalServerContainer]
        A list of OPAL server containers.

    Yields
    ------
    dict
        A dictionary mapping topic names to a list of OpalClientContainer
        instances that are subscribed to the topic.
    """
    if not opal_servers or len(opal_servers) == 0:
        raise ValueError("Missing 'opal_server' container.")

    opal_server_url = f"http://{opal_servers[0].settings.container_name}:7002"#{opal_servers[0].settings.port}"
    containers = {}  # List to store OpalClientContainer instances

    client_token = opal_servers[0].obtain_OPAL_tokens("topiced_opal_client_?x?")[
        "client"
    ]
    callbacks = json.dumps(
        {
            "callbacks": [
                [
                    f"{opal_server_url}/data/callback_report",
                    {
                        "method": "post",
                        "process_data": False,
                        "headers": {
                            "Authorization": f"Bearer {client_token}",
                            "content-type": "application/json",
                        },
                    },
                ]
            ]
        }
    )

    for topic, number_of_clients in session_matrix["topics"].items():
        for i in range(number_of_clients):
            container_name = f"opal_client_{topic}_{i+1}"  # Unique name for each client

            container = OpalClientContainer(
                OpalClientSettings(
                    image="permitio/opal-client:latest",
                    container_name=container_name,
                    container_index=i + 1,
                    opal_server_url=opal_server_url,
                    client_token=client_token,
                    default_update_callbacks=callbacks,
                    topics=topic,
                ),
                network=opal_network,
            )

            container.start()
            logger.info(
                f"Started OpalClientContainer: {container_name}, ID: {container.get_wrapped_container().id} - on topic: {topic}"
            )
            containers[topic] = containers.get(topic, [])

            assert container.wait_for_log(
                log_str="Connected to PubSub server", timeout=30
            ), f"Client {client.settings.container_name} did not connect to PubSub server."

            containers[topic].append(container)

    yield containers

    for _, clients in containers.items():
        for client in clients:
            client.stop()


def wait_sometime():
    """Pauses execution based on the environment.

    If the code is running inside GitHub Actions, it pauses execution
    for 30 seconds. Otherwise, it waits for user input to continue.

    This can be used to control the flow of execution depending on the
    environment in which the code is being executed.
    """

    if os.getenv("GITHUB_ACTIONS") == "true":
        logger.info("Running inside GitHub Actions. Sleeping for 30 seconds...")
        for secconds_ellapsed in range(30):
            time.sleep(1)
            print(f"Sleeping for \033[91m{29 - secconds_ellapsed}\033[0m seconds... \r",end="\r" if secconds_ellapsed < 29 else "\n")
    else:
        logger.info("Running on the local machine. Press Enter to continue...")
        input()  # Wait for key press


@pytest.fixture(scope="session", autouse=True)
def setup(opal_clients, policy_repo, session_matrix):
    """A setup fixture that is run once per test session.

    This fixture is automatically used by all tests, and is used to set up the
    environment for the test session. The fixture yields, allowing the tests to
    execute, and then is used to tear down the environment when the test session
    is finished.

    Parameters
    ----------
    opal_servers : List[OpalServerContainer]
        A list of OPAL server containers.
    opal_clients : List[OpalClientContainer]
        A list of OPAL client containers.
    session_matrix : dict
        A dictionary containing information about the test session.

    Yields
    ------
    None
    """
    yield
    policy_repo.cleanup(delete_ssh_key=False)
    if session_matrix["is_final"]:
        logger.info("Finalizing test session...")
        utils.remove_env("OPAL_TESTS_DEBUG")
        wait_sometime()
