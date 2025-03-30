import codecs
import os
import shutil

from git import GitCommandError, Repo

from tests.containers.settings.gitea_settings import GiteaSettings
from tests.policy_repos.gitea_policy_repo_settings import GiteaPolicyRepoSettings
from tests.policy_repos.policy_repo_base import PolicyRepoBase
from tests.policy_repos.policy_repo_settings import PolicyRepoSettings

from testcontainers.core.utils import setup_logger


class GiteaPolicyRepo(PolicyRepoBase):
    def __init__(self, settings: GiteaPolicyRepoSettings, *args):
        super().__init__()
        self.logger = setup_logger(__name__)
        self.settings = settings

    # def setup(self, settings: PolicyRepoSettings):
    #     self.settings = settings

    def setup(self):
        self.test_branch = self.settings.branch_name

    def get_repo_url(self):
        if self.settings is None:
            raise Exception("Gitea settings not set")

        return f"http://{self.settings.container_name}:{self.settings.repo_port_http}/{self.settings.username}/{self.settings.repo_name}.git"

    def clone_and_update(
        self,
        branch,
        file_name,
        file_content,
        CLONE_DIR,
        authenticated_url,
        COMMIT_MESSAGE,
    ):
        """Clone the repository, update the specified branch, and push
        changes."""
        # self.prepare_directory(CLONE_DIR)  # Clean up and prepare the directory
        print(f"Processing branch: {branch}")

        # Clone the repository for the specified branch
        print(f"Cloning branch {branch}...")
        repo = Repo.clone_from(authenticated_url, CLONE_DIR, branch=branch)

        # Create or update the specified file with the provided content
        file_path = os.path.join(CLONE_DIR, file_name)
        with open(file_path, "w") as f:
            f.write(file_content)

        # Stage the changes
        print(f"Staging changes for branch {branch}...")
        repo.git.add(A=True)  # Add all changes

        # Commit the changes if there are modifications
        if repo.is_dirty():
            print(f"Committing changes for branch {branch}...")
            repo.index.commit(COMMIT_MESSAGE)

        # Push changes to the remote repository
        print(f"Pushing changes for branch {branch}...")
        try:
            repo.git.push(authenticated_url, branch)
        except GitCommandError as e:
            print(f"Error pushing branch {branch}: {e}")
        finally:
            repo.close()
            shutil.rmtree(CLONE_DIR)

    def update_branch(self, file_name, file_content):
        temp_dir = self.settings.local_clone_path
        branch = self.test_branch

        self.logger.info(
            f"Updating branch '{branch}' with file '{file_name}' content..."
        )

        # Decode escape sequences in the file content
        file_content = codecs.decode(file_content, "unicode_escape")

        GITEA_REPO_URL = f"http://localhost:{self.settings.repo_port_http}/{self.settings.username}/{self.settings.repo_name}.git"
        username = self.settings.owner
        PASSWORD = self.settings.password
        CLONE_DIR = os.path.join(temp_dir, "branch_update")
        COMMIT_MESSAGE = "Automated update commit"

        # Append credentials to the repository URL
        authenticated_url = GITEA_REPO_URL.replace(
            "http://", f"http://{username}:{PASSWORD}@"
        )

        try:
            self.clone_and_update(
                branch,
                file_name,
                file_content,
                CLONE_DIR,
                authenticated_url,
                COMMIT_MESSAGE,
            )
            print("Operation completed successfully.")
        finally:
            # Ensure cleanup is performed regardless of success or failure
            self.cleanup(CLONE_DIR)

    def cleanup(self, *args, **kwargs):
        return super().cleanup()

    def setup_webhook(self, host, port):
        return super().setup_webhook(host, port)

    def create_webhook(self):
        return super().create_webhook()
