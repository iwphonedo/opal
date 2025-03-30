import os
import shutil
import tempfile
import time

import pytest
from testcontainers.core.utils import setup_logger

from tests import utils
from tests.fixtures.broadcasters import (
    broadcast_channel,
    kafka_broadcast_channel,
    postgres_broadcast_channel,
    redis_broadcast_channel,
)
from tests.fixtures.images import (
    cedar_image,
    opa_image,
    opal_client_image,
    opal_client_with_opa_image,
    opal_server_image,
)
from tests.fixtures.opal import (
    connected_clients,
    opal_clients,
    opal_network,
    opal_servers,
    topiced_clients,
)
from tests.fixtures.policy_repos import policy_repo

logger = setup_logger("conftest")


utils.pre_set()


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

    dir_path = tempfile.mkdtemp(prefix="opal_tests_", suffix=".tmp", dir=str(path))
    os.chmod(
        dir_path, 0o777
    )  # Set permissions to allow read/write/execute for all users
    logger.debug(f"Temporary directory created: {dir_path}")
    yield dir_path

    # Teardown: Clean up the temporary directory
    shutil.rmtree(dir_path)
    shutil.rmtree(path)
    logger.debug(f"Temporary directory removed: {dir_path}")


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

    logger.info("Initializing test session...")
    logger.debug("\n\nusing session matrix:")
    for key in session_matrix:
        logger.debug(f"{key}: {session_matrix[key]}")
    logger.debug("\n\n")

    yield
    policy_repo.cleanup()
    if session_matrix["is_final"]:
        logger.info("Finalizing test session...")
        utils.remove_env("OPAL_TESTS_DEBUG")
        utils.wait_sometime()
