import codecs
import logging
import os
import random
import shutil
import subprocess

import requests
from git import GitCommandError, Repo
from github import Auth, Github
from testcontainers.core.utils import setup_logger

from tests import utils
from tests.policy_repos.github_policy_settings import GithubPolicyRepoSettings
from tests.policy_repos.policy_repo_base import PolicyRepoBase
from tests.policy_repos.policy_repo_settings import PolicyRepoSettings


class GithubPolicyRepo(PolicyRepoBase):
    def setup_webhook(self, host, port):
        pass

    def create_webhook(self):
        pass

    def __init__(
        self,
        settings: GithubPolicyRepoSettings,
        logger: logging.Logger = setup_logger(__name__),
    ):
        self.logger = logger
        self.settings = settings

    def get_repo_url(self):
        return self.build_repo_url(self.settings.owner, self.settings.repo)

    def build_repo_url(self, owner, repo) -> str:
        if owner is None:
            raise Exception("Owner not set")

        protocol = "https"
        pat = self.settings.github_pat
        if pat:
            return f"{protocol}://{pat}@{self.settings.host}/{owner}/{repo}.git"

        raise Exception("No valid authentication method set")

    def get_source_repo_url(self):
        return self.build_repo_url(
            self.settings.source_repo_owner, self.settings.source_repo_name
        )

    def clone_initial_repo(self):
        Repo.clone_from(self.get_source_repo_url(), self.settings.local_repo_path)

    def check_repo_exists(self):
        try:
            gh = Github(auth=Auth.Token(self.settings.github_pat))
            repo_list = gh.get_user().get_repos()
            for repo in repo_list:
                if repo.full_name == self.settings.repo:
                    self.logger.debug(
                        f"Repository {self.settings.repo} already exists."
                    )
                    return True

        except Exception as e:
            self.logger.error(f"Error checking repository existence: {e}")

        return False

    def create_target_repo(self):
        if self.check_repo_exists():
            return

        try:
            gh = Github(auth=Auth.Token(self.settings.github_pat))
            gh.get_user().create_repo(self.settings.repo)
            self.logger.info(f"Repository {self.settings.repo} created successfully.")
        except Exception as e:
            self.logger.error(f"Error creating repository: {e}")

    def cleanup(self, delete_repo=True):
        try:
            if os.path.exists(self.settings.local_repo_path):
                shutil.rmtree(self.settings.local_repo_path)
                self.logger.info(
                    f"Local repository at {self.settings.local_repo_path} deleted."
                )
        except Exception as e:
            self.logger.error(f"Failed to delete local repo path: {e}")

        try:
            self.delete_test_branches()
        except Exception as e:
            self.logger.error(f"Failed to delete test branches: {e}")

        if delete_repo:
            try:
                self.delete_repo()
            except Exception as e:
                self.logger.error(f"Failed to delete remote repo: {e}")

    def delete_test_branches(self):
        try:
            self.logger.info(f"Deleting test branches from {self.settings.repo}...")

            gh = Github(auth=Auth.Token(self.settings.github_pat))
            repo = gh.get_user().get_repo(self.settings.repo)

            branches = repo.get_branches()
            for branch in branches:
                if branch.name.startswith("test-"):
                    ref = f"heads/{branch.name}"
                    repo.get_git_ref(ref).delete()
                    self.logger.info(f"Deleted branch: {branch.name}")
                else:
                    self.logger.info(f"Skipping branch: {branch.name}")

            self.logger.info("All test branches have been deleted successfully.")
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")

        return

    def generate_test_branch(self):
        self.test_branch = (
            f"test-{random.randint(1000, 9999)}{random.randint(1000, 9999)}"
        )
        os.environ["OPAL_POLICY_REPO_BRANCH"] = self.test_branch

    def create_test_branch(self):
        try:
            repo = Repo(self.settings.local_repo_path)

            if repo.is_dirty(untracked_files=True):
                raise RuntimeError(
                    "The repository has uncommitted changes. Commit or stash them before proceeding."
                )

            remote_url = self.get_repo_url()
            if "origin" in repo.remotes:
                origin = repo.remote(name="origin")
                origin.set_url(remote_url)
            else:
                origin = repo.create_remote("origin", remote_url)

            self.logger.debug(f"Origin set to: {remote_url}")

            new_branch = repo.create_head(self.test_branch)
            new_branch.checkout()

            origin.push(refspec=f"{self.test_branch}:{self.test_branch}")

            self.logger.info(
                f"Branch '{self.test_branch}' successfully created and pushed."
            )
        except GitCommandError as e:
            self.logger.error(f"Git command failed: {e}")
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")

    def delete_repo(self):
        try:
            gh = Github(auth=Auth.Token(self.settings.github_pat))
            repo = gh.get_user().get_repo(self.settings.repo)
            repo.delete()
            self.logger.debug(f"Repository {self.settings.repo} deleted successfully.")
        except Exception as e:
            self.logger.error(f"Error deleting repository: {e}")

    def setup(self):
        self.create_target_repo()
        self.clone_initial_repo()
        self.generate_test_branch()
        self.create_test_branch()

    def update_branch(self, file_name, file_content):
        self.logger.info(
            f"Updating branch '{self.test_branch}' with file '{file_name}' content..."
        )

        if file_content is not None:
            file_content = codecs.decode(file_content, "unicode_escape")

            file_path = os.path.join(self.settings.local_repo_path, file_name)
            with open(file_path, "w") as f:
                f.write(file_content)

        try:
            self.logger.debug(f"Staging changes for branch {self.test_branch}...")
            gh = Github(auth=Auth.Token(self.settings.github_pat))
            repo = gh.get_user().get_repo(self.settings.repo)
            branch_ref = f"heads/{self.test_branch}"
            ref = repo.get_git_ref(branch_ref)
            latest_commit = repo.get_git_commit(ref.object.sha)
            from github.InputGitTreeElement import InputGitTreeElement

            new_tree = repo.create_git_tree(
                [
                    InputGitTreeElement(
                        path=file_name,
                        mode="100644",
                        type="blob",
                        content=file_content,
                    )
                ],
                latest_commit.tree,
            )
            new_commit = repo.create_git_commit(
                f"Commit changes for branch {self.test_branch}",
                new_tree,
                [latest_commit],
            )
            ref.edit(new_commit.sha)
            self.logger.debug(f"Changes pushed for branch {self.test_branch}.")

        except Exception as e:
            self.logger.error(f"Error updating branch: {e}")
            return False

        return True
