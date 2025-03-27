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
    def __init__(
        self,
        settings: GithubPolicyRepoSettings,
        logger: logging.Logger = setup_logger(__name__),
    ):
        self.logger = logger
        self.settings = settings

        self.load_ssh_key()

    def load_ssh_key(self):

        if self.settings.opal_policy_repo_ssh_key_public and self.settings.opal_policy_repo_ssh_key_private:
            self.ssh_key = self.settings.opal_policy_repo_ssh_key_public
            self.private_key = self.settings.opal_policy_repo_ssh_key_private
            return
        
        if self.settings.ssh_key_path.startswith("~"):
            self.settings.ssh_key_path = os.path.expanduser(self.settings.ssh_key_path)

        if not os.path.exists(self.settings.ssh_key_path):
            self.logger.debug(f"SSH key file not found at {self.settings.ssh_key_path}")

            self.logger.debug("Generating new SSH key...")
            ssh_keys = utils.generate_ssh_key_pair()
            self.ssh_key = ssh_keys["public"]
            self.private_key = ssh_keys["private"]
            return

        try:
            with open(self.settings.ssh_key_path, "r") as ssh_key_file:
                self.ssh_key = ssh_key_file.read().strip()

            os.environ["OPAL_POLICY_REPO_SSH_KEY"] = self.ssh_key
        except Exception as e:
            self.logger.error(f"Error loading SSH key: {e}")

    def setup_webhook(self, host, port):
        self.webhook_host = host
        self.webhook_port = port

    def set_envvars(self):
        # Update .env file
        with open(".env", "a") as env_file:
            env_file.write(f'OPAL_POLICY_REPO_URL="{self.get_repo_url()}"\n')
            env_file.write(f'OPAL_POLICY_REPO_BRANCH="{self.test_branch}"\n')

        with open(".env", "a") as env_file:
            env_file.write(f'OPAL_POLICY_REPO_SSH_KEY="{self.ssh_key}"\n')

    def get_repo_url(self):
        return self.build_repo_url(self.settings.owner, self.settings.repo)

    def build_repo_url(self, owner, repo) -> str:
        if owner is None:
            raise Exception("Owner not set")

        if self.settings.protocol == "ssh" or self.settings.protocol == "git":
            return f"git@{self.settings.host}:{owner}/{repo}.git"

        if self.settings.protocol == "http" or self.settings.protocol == "https":
            if self.settings.github_pat:
                return f"{self.settings.protocol}://{self.settings.host}/{owner}/{repo}.git"

        if self.settings.password is None and self.settings.github_pat is None and self.ssh_key is None:
            raise Exception("No authentication method set")

        return f"{self.settings.protocol}://{self.settings.owner}:{self.settings.password}@{self.settings.host}:{self.settings.port}/{owner}/{repo}"

    def get_source_repo_url(self):
        return self.build_repo_url(self.settings.source_repo_owner, self.settings.source_repo_name)

    def clone_initial_repo(self):
        Repo.clone_from(self.get_source_repo_url(), self.settings.local_repo_path)

    def check_repo_exists(self):
        try:
            gh = Github(auth=Auth.Token(self.settings.github_pat))
            repo_list = gh.get_user().get_repos()
            for repo in repo_list:
                if repo.full_name == self.settings.repo:
                    self.logger.debug(f"Repository {self.settings.repo} already exists.")
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

    def fork_target_repo(self):
        if self.check_repo_exists():
            return

        self.logger.debug(f"Forking repository {self.settings.source_repo_name}...")

        if self.settings.github_pat is None:
            try:
                gh = Github(auth=Auth.Token(self.settings.github_pat))
                gh.get_user().create_fork(self.settings.source_repo_owner, self.settings.source_repo_name)
                self.logger.info(
                    f"Repository {self.settings.source_repo_name} forked successfully."
                )
            except Exception as e:
                self.logger.error(f"Error forking repository: {e}")
            return

        # Try with PAT
        try:
            headers = {"Authorization": f"token {self.settings.github_pat}"}
            response = requests.post(
                f"https://api.github.com/repos/{self.settings.source_repo_owner}/{self.settings.source_repo_name}/forks",
                headers=headers,
            )
            if response.status_code == 202:
                self.logger.info("Fork created successfully!")
            else:
                self.logger.error(f"Error creating fork: {response.status_code}")
                self.logger.debug(response.json())

        except Exception as e:
            self.logger.error(f"Error forking repository: {str(e)}")

    def cleanup(self):
        self.delete_test_branches()

    def delete_test_branches(self):
        """Deletes all branches starting with 'test-' from the specified
        repository."""

        try:
            self.logger.info(f"Deleting test branches from {self.settings.repo}...")

            # Initialize Github API
            gh = Github(auth=Auth.Token(self.settings.github_pat))

            # Get the repository
            repo = gh.get_user().get_repo(self.settings.repo)

            # Enumerate branches and delete pytest- branches
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
            # Initialize the repository
            repo = Repo(self.settings.local_repo_path)

            # Ensure the repository is clean
            if repo.is_dirty(untracked_files=True):
                raise RuntimeError(
                    "The repository has uncommitted changes. Commit or stash them before proceeding."
                )

            # Set the origin remote URL
            remote_url = f"https://github.com/{self.settings.owner}/{self.settings.repo}.git"
            if "origin" in repo.remotes:
                origin = repo.remote(name="origin")
                origin.set_url(remote_url)  # Update origin URL if it exists
            else:
                origin = repo.create_remote(
                    "origin", remote_url
                )  # Create origin remote if it doesn't exist

            self.logger.debug(f"Origin set to: {remote_url}")

            # Create and checkout the new branch
            new_branch = repo.create_head(self.test_branch)  # Create branch
            new_branch.checkout()  # Switch to the new branch

            # Push the new branch to the remote
            origin.push(refspec=f"{self.test_branch}:{self.test_branch}")

            self.logger.info(
                f"Branch '{self.test_branch}' successfully created and pushed."
            )
        except GitCommandError as e:
            self.logger.error(f"Git command failed: {e}")
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")

    def cleanup(self, delete_repo=True, delete_ssh_key=True):
        subprocess.run(["rm", "-rf", self.settings.local_repo_path], check=True)

        self.delete_test_branches()

        if delete_repo:
            self.delete_repo()

        if delete_ssh_key:
            self.delete_ssh_key()

    def delete_ssh_key(self):
        gh = Github(auth=Auth.Token(self.settings.github_pat))
        user = gh.get_user()
        keys = user.get_keys()
        for key in keys:
            if key.title == self.settings.ssh_key_name:
                key.delete()
                self.logger.debug(f"SSH key deleted: {key.title}")
                break

        self.logger.debug("All OPAL SSH keys have been deleted successfully.")

        return

    def delete_repo(self):
        try:
            gh = Github(auth=Auth.Token(self.settings.github_pat))
            repo = gh.get_user().get_repo(self.settings.repo)
            repo.delete()
            self.logger.debug(f"Repository {self.settings.repo} deleted successfully.")
        except Exception as e:
            self.logger.error(f"Error deleting repository: {e}")

    def setup(self):
        self.clone_initial_repo()

        if self.settings.should_fork:
            self.fork_target_repo()
        else:
            self.create_target_repo()

        self.generate_test_branch()
        self.create_test_branch()

    def add_ssh_key(self):
        gh = Github(auth=Auth.Token(self.settings.github_pat))
        user = gh.get_user()
        keys = user.get_keys()
        for key in keys:
            if key.title == self.settings.ssh_key_name:
                return

        key = user.create_key(self.settings.ssh_key_name, self.ssh_key)
        self.logger.info(f"SSH key added: {key.title}")

    def create_webhook(self):
        try:
            gh = Github(auth=Auth.Token(self.settings.github_pat))
            self.logger.info(
                f"Creating webhook for repository {self.settings.owner}/{self.settings.repo}"
            )
            repo = gh.get_user().get_repo(f"{self.settings.repo}")
            url = utils.create_localtunnel(self.webhook_port)
            self.logger.info(f"Webhook URL: {url}")
            self.github_webhook = repo.create_hook(
                "web",
                {
                    "url": f"{url}/webhook",
                    "content_type": "json",
                    f"secret": "abc123",
                    "insecure_ssl": "1",
                },
                events=["push"],
                active=True,
            )
            self.logger.info("Webhook created successfully.")
        except Exception as e:
            self.logger.error(f"Error creating webhook: {e}")

    def delete_webhook(self):
        try:
            gh = Github(auth=Auth.Token(self.settings.github_pat))
            repo = gh.get_user().get_repo(f"{self.settings.repo}")
            repo.delete_hook(self.github_webhook.id)
            self.logger.info("Webhook deleted successfully.")
        except Exception as e:
            self.logger.error(f"Error deleting webhook: {e}")

    def update_branch(self, file_name, file_content):
        self.logger.info(
            f"Updating branch '{self.test_branch}' with file '{file_name}' content..."
        )

        # Decode escape sequences in the file content
        if file_content is not None:
            file_content = codecs.decode(file_content, "unicode_escape")

            # Create or update the specified file with the provided content
            file_path = os.path.join(self.settings.local_repo_path, file_name)
            with open(file_path, "w") as f:
                f.write(file_content)

        # if file_content is None:
        #     with open(file_path, "r") as f:
        #         file_content = f.read()

        try:
            # Stage the changes
            self.logger.debug(f"Staging changes for branch {self.test_branch}...")
            gh = Github(auth=Auth.Token(self.settings.github_pat))
            repo = gh.get_user().get_repo(self.settings.repo)
            branch_ref = f"heads/{self.test_branch}"
            ref = repo.get_git_ref(branch_ref)
            latest_commit = repo.get_git_commit(ref.object.sha)
            base_tree = latest_commit.tree
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
                base_tree,
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

    def remove_webhook(self):
        self.github_webhook.delete()
