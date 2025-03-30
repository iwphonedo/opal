import os

import pytest
from testcontainers.core.network import Network
from testcontainers.core.utils import setup_logger

from tests.containers.gitea_container import GiteaContainer
from tests.containers.settings.gitea_settings import GiteaSettings
from tests.policy_repos.gitea_policy_repo import GiteaPolicyRepo
from tests.policy_repos.gitea_policy_repo_settings import GiteaPolicyRepoSettings
from tests.policy_repos.github_policy_repo import GithubPolicyRepo
from tests.policy_repos.github_policy_settings import GithubPolicyRepoSettings
from tests.policy_repos.policy_repo_base import PolicyRepoBase
from tests.policy_repos.policy_repo_factory import (
    PolicyRepoFactory,
    SupportedPolicyRepo,
)
from tests.policy_repos.policy_repo_settings import PolicyRepoSettings
from tests.settings import pytest_settings

logger = setup_logger("policy_repos")


# @pytest.fixture(scope="session")
def gitea_settings():
    """Returns a GiteaSettings object with default values for the Gitea
    container name, repository name, temporary directory, and data directory.

    This fixture is used to create a Gitea container for testing and to
    initialize the repository settings for the policy repository.

    :return: A GiteaSettings object with default settings.
    """
    return GiteaSettings(
        container_name="gitea_server",
        repo_name="test_repo",
        temp_dir=os.path.join(os.path.dirname(__file__), "temp"),
        data_dir=os.path.join(os.path.dirname(__file__), "../policies"),
    )


# @pytest.fixture(scope="session")
def gitea_server(opal_network: Network):
    """Creates a Gitea container and initializes a test repository.

    The Gitea container is created with the default settings for the
    container name, repository name, temporary directory, and data
    directory. The container is then started and the test repository is
    initialized.

    The fixture yields the GiteaContainer object, which can be used to
    interact with the Gitea container.

    :param opal_network: The network to create the container on.
    :param gitea_settings: The settings for the Gitea container.
    :return: The GiteaContainer object.
    """

    gitea_container = GiteaContainer(settings=gitea_settings(), network=opal_network)

    gitea_container.deploy_gitea()
    gitea_container.init_repo()

    yield gitea_container


def create_github_policy_repo_settings(temp_dir: str, session_matrix):
    # logger.info("Creating GithubPolicyRepoSettings...")
    # logger.info("\n\n\n\n")
    # logger.info(session_matrix)
    # logger.info("\n\n\n\n")

    # input()

    return GithubPolicyRepoSettings(
        temp_dir=temp_dir,
        local_clone_path=temp_dir,
        source_repo_owner=session_matrix["source_repo_owner"],
        source_repo_name=session_matrix["source_repo_name"],
        repo_name=session_matrix["repo_name"],
        owner=session_matrix["repo_owner"],
        ssh_key_path=session_matrix["ssh_key_path"],
        pat=session_matrix["github_pat"],
        webhook_secret=session_matrix["webhook_secret"],
        should_fork=False,
        # should_fork = session_matrix["should_fork"],
        password=session_matrix["repo_password"],
        opal_policy_repo_ssh_key_public=session_matrix[
            "opal_policy_repo_ssh_key_public"
        ],
        opal_policy_repo_ssh_key_private=session_matrix[
            "opal_policy_repo_ssh_key_private"
        ],
    )


def create_gitea_policy_repo_settings(
    temp_dir: str, session_matrix, gitea_settings: GiteaSettings
):
    """Creates a Gitea policy repository settings object.

    This method creates a Gitea policy repository settings object based
    on the given parameters. The object is initialized with the default
    values for the local clone path, owner, repository name, branch
    name, container name, repository host, repository ports, password,
    SSH key path, source repository owner and name, whether to fork the
    repository, whether to create the repository, and webhook secret.

    :param temp_dir: The temporary directory to use for the policy
        repository.
    :param session_matrix: The session matrix to use for the policy
        repository.
    :param gitea_settings: The settings for the Gitea container.
    :return: The GiteaPolicyRepoSettings object.
    """

    return GiteaPolicyRepoSettings(
        local_clone_path=temp_dir,
        owner=gitea_settings.username,
        repo_name=gitea_settings.repo_name,
        branch_name="master",
        container_name=gitea_settings.container_name,
        repo_host="localhost",
        repo_port_http=gitea_settings.port_http,
        repo_port_ssh=gitea_settings.port_ssh,
        password=gitea_settings.password,
        pat=None,
        ssh_key_path=pytest_settings.ssh_key_path,
        source_repo_owner=gitea_settings.username,
        source_repo_name=gitea_settings.repo_name,
        should_fork=False,
        should_create_repo=True,
        webhook_secret=pytest_settings.webhook_secret,
    )


# @pytest.fixture(scope="session")
def policy_repo_settings(
    temp_dir: str,
    session_matrix,
    opal_network,
    policy_repo_type=SupportedPolicyRepo.GITHUB,
):
    """Creates a policy repository settings object based on the specified type
    of policy repository.

    This method takes in the following parameters:

    :param temp_dir: The temporary directory to use for the policy repository.
    :param session_matrix: The session matrix to use for the test.
    :param opal_network: The network to create the container on.
    :param policy_repo_type: The type of policy repository to create. Defaults to SupportedPolicyRepo.GITHUB.

    :return: The policy repository settings object.
    """
    gitea_server_settings = None

    if policy_repo_type == SupportedPolicyRepo.GITEA:
        # gitea_server = request.getfixturevalue("gitea_server")
        gitea_server_settings = next(gitea_server(opal_network))

    map = {
        SupportedPolicyRepo.GITHUB: create_github_policy_repo_settings,
        SupportedPolicyRepo.GITEA: lambda temp_dir, session_matrix: create_gitea_policy_repo_settings(
            temp_dir, session_matrix, gitea_server_settings.settings
        ),
    }

    yield (map[policy_repo_type](temp_dir, session_matrix), gitea_server_settings)


@pytest.fixture(scope="session")
def policy_repo(temp_dir: str, session_matrix, opal_network, request):
    """Creates a policy repository for testing.

    This fixture creates a policy repository based on the configuration
    specified in pytest.ini. The repository is created with the default
    branch name "master" and is initialized with the policies from the
    source repository specified in pytest.ini.

    The fixture yields the PolicyRepoBase object, which can be used to
    interact with the policy repository.

    :param gitea_settings: The settings for the Gitea container.
    :param temp_dir: The temporary directory to use for the policy
        repository.
    :param request: The pytest request object.
    :return: The PolicyRepoBase object.
    """

    settings, server = next(
        policy_repo_settings(
            temp_dir, session_matrix, opal_network, session_matrix["repo_provider"]
        )
    )

    policy_repo = PolicyRepoFactory(
        session_matrix["repo_provider"],
    ).get_policy_repo(
        settings,
        logger,
    )

    # policy_repo.setup(gitea_settings)
    policy_repo.setup()
    yield policy_repo

    if server is not None:
        server.get_wrapped_container().kill()
        server.get_wrapped_container().remove(v=True, force=True)
