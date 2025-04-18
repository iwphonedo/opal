Got it! If you'd like, I can incorporate code snippets or provide clarifications. Just let me know what specific details or examples you'd like me to include. Here's the README file in Markdown format:

---

# Tests

The tests folder contains integration and unit tests for OPAL. These tests ensure the proper functionality and reliability of OPAL across various components and scenarios. Below is an overview of the test structure, utilities, and execution methods.

## Test Structure

- **`tests/containers`**: Configurations and setups for containerized environments used in testing OPAL, including Docker and Kubernetes configurations.
- **`tests/data-fetchers`**: OPAL data fetchers used in the tests to fetch data from various sources, such as PostgreSQL, MongoDB, etc.
- **`tests/docker`**: Dockerfiles and related files used to build Docker images for the tests.
- **`tests/policies`**: Policies written in REGO used to verify that OPAL functions correctly.
- **`tests/policy_repos`**: Providers managing policy repositories on platforms such as Gitea, GitHub, GitLab, and others. Additional platforms should implement a class derived from `PolicyRepoBase` (e.g., Bitbucket).
- **`tests/app-tests`**: Integration tests running OPAL with a sample service to verify correct configuration.
- **`tests/policy_stores`**: Test setups to validate support for policy decision engines such as OPA, Cedar, OpenFGA, etc.
- **`conftest.py`**: Fixtures shared across multiple tests for consistent test environments.

The tests are built using [Pytest](https://pytest.org/en/latest/) and leverage [testcontainers](https://testcontainers.org/) to build and run Docker images.

## Infrastructure of the Testing System

### Settings

The `settings.py` file includes a `TestSettings` class for configuring global test settings. This class allows you to define:

- Test data location.
- Docker network configuration.
- Other environment settings.

### Utilities

The `utils.py` file contains a `Utils` class for simplifying test writing. It provides methods for:

- Creating temporary directories.
- Copying files.
- Other common tasks.

### Using the `session_matrix`

The `session_matrix` feature allows you to define and manage test scenarios across multiple configurations. This is particularly useful for validating OPAL's behavior under various conditions.

#### Using the `is_final` Property

The `is_final` property within the `session_matrix` helps identify if a particular test session represents the last stage of a given scenario. This can be used to perform cleanup tasks or additional validations at the end of a test sequence.

Example:

```python
def test_example(session_matrix):
    if session_matrix.is_final:
        # Perform cleanup or final assertions
        print("Final session reached")
```

## Writing Your Own Tests

To write a test, include `opal_servers` and `opal_clients` as parameters in your test function. These will automatically be populated with available OPAL servers and clients. For example:

```python
def test_custom_policy(opal_servers, opal_clients):
    server = opal_servers[0]
    client = opal_clients[0]
    # Add your test logic here
```

## Running the Tests

To execute the tests, run the `run.sh` script from the root directory of the repository. This script sets up the environment and executes all tests:

```bash
./run.sh
```

## OPAL API Reference

Refer to the [OPAL API Documentation](https://opal-v2.permit.io/redoc#tag/Bundle-Server/operation/get_policy_policy_get) for additional details on endpoints and functionality.

---

Let me know if you'd like to include specific code examples or any other details!
