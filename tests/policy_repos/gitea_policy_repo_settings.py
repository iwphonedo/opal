import os
from tests.policy_repos.supported_policy_repo import SupportedPolicyRepo
from testcontainers.core.utils import setup_logger

class GiteaPolicyRepoSettings:
    def __init__(
        self,
        local_clone_path: str | None = None,
        owner: str | None = None,
        username: str | None = None,
        repo_name: str | None = None,
        branch_name: str | None = None,
        container_name: str | None = None,
        repo_host: str | None = None,
        repo_port_http: int | None = None,
        repo_port_ssh: int | None = None,
        password: str | None = None,
        pat: str | None = None,
        ssh_key_path: str | None = None,
        source_repo_owner: str | None = None,
        source_repo_name: str | None = None,
        should_fork: bool = False,
        should_create_repo: bool = False,  # if True, will create the repo, if the should_fork is False.
        # If should_fork is True, it will fork and not create the repo from scratch.
        # if False, the an existing repository is expected
        webhook_secret: str | None = None,
    ):
        
        """
        GiteaPolicyRepoSettings initialization.

        This method is used to initialize the Gitea policy repository settings.
        It takes in the following parameters:

        Args:
        local_clone_path (str, optional): The local path to clone the repo to. Defaults to None.
        owner (str, optional): The owner of the repo. Defaults to None.
        repo_name (str, optional): The name of the repo. Defaults to None.
        branch_name (str, optional): The name of the branch. Defaults to None.
        repo_host (str, optional): The host of the repo. Defaults to None.
        repo_port_http (int, optional): The HTTP port of the repo. Defaults to None.
        repo_port_ssh (int, optional): The SSH port of the repo. Defaults to None.
        password (str, optional): The password to use for authentication. Defaults to None.
        pat (str, optional): The personal access token to use for authentication. Defaults to None.
        ssh_key_path (str, optional): The path to the SSH key to use for authentication. Defaults to None.
        source_repo_owner (str, optional): The owner of the source repo. Defaults to None.
        source_repo_name (str, optional): The name of the source repo. Defaults to None.
        should_fork (bool, optional): Whether to fork the repo. Defaults to False.
        should_create_repo (bool, optional): Whether to create the repo. Defaults to False.
        webhook_secret (str, optional): The secret to use for the webhook. Defaults to None.

        This method sets the following attributes of the Gitea policy repository settings:
        local_clone_path, owner, repo_name, branch_name, repo_host, repo_port_http, repo_port_ssh, password, pat, ssh_key_path, source_repo_owner, source_repo_name, should_fork, should_create_repo, webhook_secret.
        """
        
        self.policy_repo_type = SupportedPolicyRepo.GITEA

        self.logger = setup_logger(__name__)

        # Load from environment variables
        self.load_from_env()

        # Set attributes
        self.username = username if username else self.username
        self.local_clone_path = local_clone_path if local_clone_path else self.local_clone_path
        self.owner = owner if owner else self.owner
        self.repo_name = repo_name if repo_name else self.repo_name
        self.branch_name = branch_name if branch_name else self.branch_name
        self.container_name = container_name if container_name else self.container_name
        self.repo_host = repo_host if repo_host else self.repo_host
        self.repo_port_http = repo_port_http if repo_port_http else self.repo_port_http
        self.repo_port_ssh = repo_port_ssh if repo_port_ssh else self.repo_port_ssh
        self.password = password if password else self.password
        self.pat = pat if pat else self.pat
        self.ssh_key_path = ssh_key_path if ssh_key_path else self.ssh_key_path
        self.source_repo_owner = source_repo_owner if source_repo_owner else self.source_repo_owner
        self.source_repo_name = source_repo_name if source_repo_name else self.source_repo_name
        self.should_fork = should_fork if should_fork else self.should_fork
        self.should_create_repo = should_create_repo if should_create_repo else self.should_create_repo
        self.webhook_secret = webhook_secret if webhook_secret else self.webhook_secret

        self.validate_dependencies()

    def load_from_env(self):
        """
        Loads environment variables into the Gitea policy repository settings.

        This method retrieves various environment variables required for configuring
        the Gitea policy repository settings and assigns them to the corresponding 
        attributes of the settings object. It provides flexibility to configure 
        repository details, authentication credentials, and other configurations 
        through environment variables.

        Attributes set by this method:
        - owner: The owner of the target repository.
        - github_pat: The GitHub personal access token for accessing the repository.
        - ssh_key_path: The path to the SSH key used for repository access.
        - repo: The name of the target repository.
        - source_repo_owner: The owner of the source repository.
        - source_repo_name: The name of the source repository.
        - webhook_secret: The secret used for authenticating webhooks.
        - repo_host: The host address for the Gitea server.
        - repo_port_http: The HTTP port for the Gitea server.
        - repo_port_ssh: The SSH port for the Gitea server.
        - password: The password for accessing the Gitea repository.
        - pat: The personal access token for the Gitea repository.
        - branch_name: The name of the branch in the Gitea repository.
        - should_fork: Whether to fork the Gitea repository.
        - should_create_repo: Whether to create the Gitea repository.
        - local_clone_path: The local path to clone the Gitea repository.
        """

        # Load from environment variables
        self.username = os.getenv("gitea_username", "permitAdmin")
        self.owner = os.getenv("OPAL_TARGET_ACCOUNT", None)
        self.github_pat = os.getenv("OPAL_GITHUB_PAT", None)
        self.ssh_key_path = os.getenv("OPAL_PYTEST_POLICY_REPO_SSH_KEY_PATH", "~/.ssh/id_rsa")
        self.repo = os.getenv("OPAL_TARGET_REPO_NAME", "opal-example-policy-repo")
        self.source_repo_owner = os.getenv("OPAL_SOURCE_ACCOUNT", "permitio")
        self.source_repo_name = os.getenv("OPAL_SOURCE_REPO_NAME", "opal-example-policy-repo")
        self.webhook_secret: str = os.getenv("OPAL_WEBHOOK_SECRET", "xxxxx")

        self.repo_host = os.getenv("OPAL_GITEA_HOST", "127.0.0.1")
        self.repo_port_http = os.getenv("OPAL_GITEA_PORT_HTTP", 3000)
        self.repo_port_ssh = os.getenv("OPAL_GITEA_PORT_SSH", 22)

        self.container_name = os.getenv("OPAL_GITEA_CONTAINER_NAME", "gitea_server")

        self.password = os.getenv("OPAL_GITEA_PASSWORD", "password")
        self.pat = os.getenv("OPAL_GITEA_PAT", "pat")
        self.ssh_key_path = os.getenv("OPAL_GITEA_SSH_KEY_PATH", "~/.ssh/id_rsa")
        self.branch_name = os.getenv("OPAL_GITEA_BRANCH_NAME", "main")
        self.should_fork = os.getenv("OPAL_GITEA_FORK", False)
        self.should_create_repo = os.getenv("OPAL_GITEA_CREATE_REPO", False)

        self.webhook_secret: str = os.getenv("OPAL_WEBHOOK_SECRET", "xxxxx")

        self.local_clone_path = os.getenv("OPAL_GITEA_LOCAL_CLONE_PATH", None)

        self.source_repo_owner = os.getenv("OPAL_SOURCE_ACCOUNT", "permitio")
        self.source_repo_name = os.getenv("OPAL_SOURCE_REPO_NAME", "opal-example-policy-repo")  
        
    def validate_dependencies(self):
        """Validate required dependencies before starting the server."""
        if not self.local_clone_path:
            raise ValueError("OPAL_GITEA_LOCAL_CLONE_PATH is required.")
        self.logger.info(f"Gitea policy repo settings | Dependencies validated successfully.")