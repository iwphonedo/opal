import os
import subprocess
import time
import argparse
import sys
import shutil

# Define current_folder as a global variable
current_folder = os.path.dirname(os.path.abspath(__file__))

uid = 502
gid = 1000

def cleanup(_temp_dir):
        if os.path.exists(_temp_dir):
            shutil.rmtree(_temp_dir)

def prepare_temp_dir():
    """
    Creates a 'temp' folder next to the running script. If it exists, deletes it recursively and recreates it.

    :return: Absolute path of the created 'temp' folder.
    """
    temp_dir = os.path.join(current_folder, 'temp')

    cleanup(temp_dir)

    os.makedirs(temp_dir)
    data_dir = os.path.join(temp_dir, 'data')
    os.makedirs(data_dir)

    return temp_dir

def run_script(script_name, temp_dir, additional_args=None):
    """
    Runs a Python script from the same folder as this script, passing the temp_dir as an argument.

    :param script_name: Name of the Python script to run (e.g., 'script.py').
    :param temp_dir: Absolute path to the 'temp' folder.
    :param additional_args: List of additional arguments to pass to the script.
    """
    script_path = os.path.join(current_folder, script_name)

    if not os.path.exists(script_path):
        print(f"Error: The script '{script_name}' does not exist in the current folder.")
        sys.exit(1)

    try:
        command = ["python", script_path, "--temp_dir", temp_dir]
        if additional_args:
            command.extend(additional_args)

        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: An error occurred while running the script '{script_name}': {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Run deployment and testing scripts.")
    parser.add_argument("--deploy", action="store_true", help="Include deployment steps before testing.")
    parser.add_argument("--with_broadcast", action="store_true", help="Use broadcast channel.")
    args = parser.parse_args()

    # Prepare the 'temp' directory
    temp_dir = prepare_temp_dir()
    #temp_dir = "/Users/israelw/opal-e2e-tests/opal/new_pytest_env/temp"

    network_name = "opal_test"
    gitea_container_name = "gitea_permit"
    gitea_container_port = 3000
    gitea_username = "permitAdmin"
    gitea_password = "Aa123456"
    gitea_repo_name = "opal-example-policy-repo"

    if args.deploy:
        print("Starting deployment...")
        #Running gitea_docker_py.py with additional arguments
        run_script(
            "gitea_docker_py.py",
            temp_dir,
            additional_args=[
                "--user_name", "permitAdmin",
                "--email", "permit@gmail.com",
                "--password", gitea_password,
                "--network_name", network_name,
                "--user_UID", str(uid),
                "--user_GID", str(gid)
            ]
        )
        time.sleep(10)

        run_script("init_repo.py", temp_dir,
                additional_args=[
                "--repo_name", gitea_repo_name,
                "--gitea_base_url", f"http://localhost:{gitea_container_port}/api/v1",
                "--user_name", gitea_username,
                "--data_dir", current_folder,
            ])
        time.sleep(10)
        if args.with_broadcast:
            run_script("opal_docker_py.py", temp_dir, 
                    additional_args=[
                    "--network_name", network_name,
                    "--OPAL_POLICY_REPO_URL", f"http://{gitea_container_name}:{gitea_container_port}/{gitea_username}/{gitea_repo_name}.git",
                    "--with_broadcast"
                    ])
        else:
            run_script("opal_docker_py.py", temp_dir, 
                    additional_args=[
                    "--network_name", network_name,
                    "--OPAL_POLICY_REPO_URL", f"http://{gitea_container_name}:{gitea_container_port}/{gitea_username}/{gitea_repo_name}.git"
                    ])
        time.sleep(20)

    print("Starting testing...")
    run_script("test.py", temp_dir,
               [
               "--branches", "master",
               "--locations", "8.8.8.8,US", "77.53.31.138,SE", "210.2.4.8,CN",
               "--gitea_user_name", gitea_username,
               "--gitea_password", gitea_password,
               "--gitea_repo_url", f"http://localhost:{gitea_container_port}/{gitea_username}/{gitea_repo_name}",
               "--OPA_base_url", "http://localhost:8181/",
               "--policy_URI", "v1/data/app/rbac/allow"
               ]
               )

    cleanup(os.path.join(current_folder, 'temp'))


if __name__ == "__main__":
    main()