import logging
import os
from enum import Enum

from testcontainers.core.utils import setup_logger

from tests.policy_repos.gitea_policy_repo import GiteaPolicyRepo
from tests.policy_repos.github_policy_repo import GithubPolicyRepo
from tests.policy_repos.gitlab_policy_repo import GitlabPolicyRepo
from tests.policy_repos.policy_repo_base import PolicyRepoBase
from tests.policy_repos.policy_repo_settings import PolicyRepoSettings
from tests.policy_repos.supported_policy_repo import SupportedPolicyRepo


# Factory class to create a policy repository object based on the type of policy repository.
class PolicyRepoFactory:
    def __init__(self, policy_repo: str = SupportedPolicyRepo.GITEA):
        """
        :param policy_repo: The type of policy repository. Defaults to GITEA.
        """
        self.assert_exists(policy_repo)

        self.policy_repo = policy_repo

    def get_policy_repo(
        self,
        settings,
        logger: logging.Logger = setup_logger(__name__),
    ) -> GithubPolicyRepo | GiteaPolicyRepo:
        factory = {
            SupportedPolicyRepo.GITEA: GiteaPolicyRepo,
            SupportedPolicyRepo.GITHUB: GithubPolicyRepo,
            SupportedPolicyRepo.GITLAB: GitlabPolicyRepo,
        }

        assert settings is not None, "Settings must be provided"
        assert settings.policy_repo_type == self.policy_repo, (
            f"Settings policy_repo_type must be {self.policy_repo}, "
            f"but got {settings.policy_repo_type}"
        )

        return factory[SupportedPolicyRepo(self.policy_repo)](settings)

    def assert_exists(self, policy_repo: str) -> bool:
        try:
            source_enum = SupportedPolicyRepo(policy_repo)
        except ValueError:
            raise ValueError(
                f"Unsupported REPO_SOURCE value: {policy_repo}. Must be one of {[e.value for e in SupportedPolicyRepo]}"
            )
