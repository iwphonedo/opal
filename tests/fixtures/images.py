import pytest
from settings import pytest_settings

import docker
from tests import utils


@pytest.fixture(scope="session")
def opal_server_image(session_matrix):
    """Builds a Docker image for the OPAL server in debug mode.

    Yields the name of the built image.

    This fixture is used to provide a working OPAL server image for the
    tests.
    """

    docker_client = docker.from_env()
    image_name = "opal_server_debug_local:latest"

    image = None
    if (not session_matrix["is_first"]) or pytest_settings["skip_rebuild_images"]:
        exists = any(image_name in image.tags for image in docker_client.images.list())
        if exists:
            image = docker_client.images.get(image_name)

    if not image:
        image = utils.build_docker_image("Dockerfile.server.local", image_name)

    yield image_name

    if session_matrix["is_final"]:
        # Optionally, clean up the image after the test session
        try:
            image.remove(force=True)
            print(f"Docker image '{image.id}' removed.")
        except Exception as cleanup_error:
            print(
                f"Failed to remove Docker image '{image_name}'{image.id}: {cleanup_error}"
            )


@pytest.fixture(scope="session")
def opa_image():
    """Builds a Docker image containing the Open Policy Agent (OPA) binary.

    Yields the name of the built image.

    This fixture is used to provide a working OPA image for the tests.
    """
    docker_client = docker.from_env()
    image_name = "opa"

    yield utils.build_docker_image("Dockerfile.opa", image_name)

    # Optionally, clean up the image after the test session
    try:
        docker_client.images.remove(image=image_name, force=True)
        print(f"Docker image '{image_name}' removed.")
    except Exception as cleanup_error:
        print(f"Failed to remove Docker image '{image_name}': {cleanup_error}")


@pytest.fixture(scope="session")
def cedar_image():
    """Builds a Docker image containing the Cedar binary.

    Yields the name of the built image.

    This fixture is used to provide a working Cedar image for the tests.
    """
    docker_client = docker.from_env()
    image_name = "cedar"

    yield utils.build_docker_image("Dockerfile.cedar", image_name)

    # Optionally, clean up the image after the test session
    try:
        docker_client.images.remove(image=image_name, force=True)
        print(f"Docker image '{image_name}' removed.")
    except Exception as cleanup_error:
        print(f"Failed to remove Docker image '{image_name}': {cleanup_error}")


@pytest.fixture(scope="session")
def opal_client_image():
    """Builds a Docker image containing the OPAL client binary.

    Yields the name of the built image.

    This fixture is used to provide a working OPAL client image for the
    tests.
    """
    docker_client = docker.from_env()
    image_name = "opal_client_debug_local"

    yield utils.build_docker_image("Dockerfile.client.local", image_name)

    # Optionally, clean up the image after the test session
    try:
        docker_client.images.remove(image=image_name, force=True)
        print(f"Docker image '{image_name}' removed.")
    except Exception as cleanup_error:
        print(f"Failed to remove Docker image '{image_name}': {cleanup_error}")
