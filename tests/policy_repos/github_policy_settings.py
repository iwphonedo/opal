import os

from testcontainers.core.utils import setup_logger

from tests.policy_repos.supported_policy_repo import SupportedPolicyRepo


class GithubPolicyRepoSettings:
    """GithubPolicyRepoSettings class.

    This class is used to store the settings for the GithubPolicyRepo.
    It is initialized with the following parameters:

    Args:
        temp_dir (str): Path of the temporary directory to clone the repo to.
        local_clone_path (str, optional): The local path to clone the repo to. Defaults to None.
        owner (str, optional): The owner of the repo. Defaults to None.
        password (str, optional): The password to use for authentication. Defaults to None.
        pat (str, optional): The personal access token to use for authentication. Defaults to None.
        repo_name (str, optional): The name of the repo. Defaults to None.
        source_repo_owner (str, optional): The owner of the source repo. Defaults to None.
        source_repo_name (str, optional): The name of the source repo. Defaults to None.
        ssh_key_path (str, optional): The path to the SSH key to use for authentication. Defaults to None.
        should_fork (bool, optional): Whether to fork the repo. Defaults to False.
        webhook_secret (str, optional): The secret to use for the webhook. Defaults to None.
    """

    def __init__(
        self,
        temp_dir: str,
        local_clone_path: str | None = None,
        owner: str | None = None,
        password: str | None = None,
        pat: str | None = None,
        repo_name: str | None = None,
        source_repo_owner: str | None = None,
        source_repo_name: str | None = None,
        ssh_key_path: str | None = None,
        should_fork: bool | None = False,
        webhook_secret: str | None = None,
        opal_policy_repo_ssh_key_public: str | None = None,
        opal_policy_repo_ssh_key_private: str | None = None,
    ):
        """GithubPolicyRepoSettings initialization.

        This class is used to store the settings for the GithubPolicyRepo.
        It is initialized with the following parameters:

        Args:
        temp_dir (str): Path of the temporary directory to clone the repo to.
        local_clone_path (str, optional): The local path to clone the repo to. Defaults to None.
        owner (str, optional): The owner of the repo. Defaults to None.
        password (str, optional): The password to use for authentication. Defaults to None.
        pat (str, optional): The personal access token to use for authentication. Defaults to None.
        repo_name (str, optional): The name of the repo. Defaults to None.
        source_repo_owner (str, optional): The owner of the source repo. Defaults to None.
        source_repo_name (str, optional): The name of the source repo. Defaults to None.
        ssh_key_path (str, optional): The path to the SSH key to use for authentication. Defaults to None.
        should_fork (bool, optional): Whether to fork the repo. Defaults to False.
        webhook_secret (str, optional): The secret to use for the webhook. Defaults to None.
        """

        self.policy_repo_type: str = SupportedPolicyRepo.GITHUB

        # Set the logger
        self.logger = setup_logger(__name__)

        # Load environment variables
        self.load_from_env()

        # Set the protocol, host, and port for the repo
        self.protocol = "git"
        self.host = "github.com"
        self.port = 22

        # Set the temporary directory to clone the repo to
        self.temp_dir = temp_dir

        # Set the name of the SSH key to use
        self.ssh_key_name = "OPAL_PYTEST"

        # Set the owner and password of the repo
        self.owner = owner if owner else self.owner
        self.password = password

        # Set the personal access token to use for authentication
        self.github_pat = pat if pat else self.github_pat

        # Set the name of the repo
        self.repo = repo_name if repo_name else self.repo

        # Set the owner and name of the source repo
        self.source_repo_owner = (
            source_repo_owner if source_repo_owner else self.source_repo_owner
        )
        self.source_repo_name = (
            source_repo_name if source_repo_name else self.source_repo_name
        )

        # Set the local path to clone the repo to
        self.local_repo_path = os.path.join(temp_dir, self.source_repo_name)

        # Set the path to the SSH key to use for authentication
        self.ssh_key_path = ssh_key_path if ssh_key_path else self.ssh_key_path

        # Set whether to fork the repo
        self.should_fork = should_fork

        # Set the secret to use for the webhook
        self.webhook_secret = webhook_secret if webhook_secret else self.webhook_secret

        # Set the public and private SSH keys
        self.opal_policy_repo_ssh_key_public = opal_policy_repo_ssh_key_public
        self.opal_policy_repo_ssh_key_private = opal_policy_repo_ssh_key_private

        # Validate the dependencies and load the SSH key
        self.validate_dependencies()

    def load_from_env(self):
        self.owner = os.getenv("OPAL_TARGET_ACCOUNT", None)
        self.github_pat = os.getenv("OPAL_GITHUB_PAT", None)
        self.ssh_key_path = os.getenv(
            "OPAL_PYTEST_POLICY_REPO_SSH_KEY_PATH", "~/.ssh/id_rsa"
        )
        self.repo = os.getenv("OPAL_TARGET_REPO_NAME", "opal-example-policy-repo")
        self.source_repo_owner = os.getenv("OPAL_SOURCE_ACCOUNT", "ariWeinberg")
        self.source_repo_name = os.getenv(
            "OPAL_SOURCE_REPO_NAME", "opal-example-policy-repo"
        )
        self.webhook_secret: str = os.getenv("OPAL_WEBHOOK_SECRET", "xxxxx")

    def validate_dependencies(self):
        if (
            not self.password
            and not self.github_pat
            and not self.ssh_key_path
            and not self.opal_policy_repo_ssh_key_private
        ):
            self.logger.error("No password or Github PAT or SSH key provided.")
            raise Exception("No authentication method provided.")
