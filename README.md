# API

## Table of Contents

1. [Developer Quickstart](#developer-quickstart)
2. [Tests](#tests)
3. [Project Structure](#project-structure)
4. [VScode Extensions](#vscode-extensions)
5. [Workflows](#workflows)
6. [Contributing](/CONTRIBUTING.md)
7. [License](/LICENSE)

## Developer Quickstart

1) Create virtual environment ([Python Download Link](https://www.python.org/downloads/))

    ```bash
    python3.12 -m venv venv
    ```

2) Activate virtual environment

    ```bash
    source venv/bin/activate
    ```

3) Install dependencies

    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install -r dev-requirements.txt
    ```

4) Run the pre-commit hook to verify everything is working

    ```bash
    pre-commit run --all-files
    ```

5) Start the server

    ```bash
    fastapi dev src/app/main.py
    ```

6) Congrats! It's working! 🎉

    - **Documentation:** http://127.0.0.1:8000/docs
    - Health Check: http://127.0.0.1:8000/api/v1/health/ping
    - Root API URL: http://127.0.0.1:8000/api/v1

## Tests

### Run Tests

```bash
pytest
```

### Code Coverage Report

```bash
pytest
open htmlcov/index.html
```

### Test Organization

All tests are located in `tests/`. The structure of the `tests/` directory mirrors the `src/app/` directory structure.

## Project Structure

```
src/
└── app
    ├── api
    │   └── v1                  # API Version 1 routes (/v1)
    |       |                   # ------------------------- #
    │       ├── health.py       # /health routes
    │       └── templates.py    # /templates routes
    |
    ├── core                    # Core Application Logic
    |   |                       # ---------------------- #
    │   ├── cdktf/              # CDKTF libraries
    │   └── logger.py           # Shared logger utility
    | 
    ├── enums                   # Enums (Constants)
    |   |                       # ------ #
    │   ├── providers.py        # Defined cloud providers
    │   └── specs.py            # Preset VM hardware configurations
    |
    ├── schemas                 # API Schema (Objects)
    |   |                       # ------------------ #
    │   ├── openlabs.py         # OpenLabs network objects
    │   └── templates.py        # Template objects
    |
    └── validators              # Data Validation
    |   |                       # --------------- #
    |   └── network.py          # Networking config input validation
    |
    └── main.py                 # Main App Entry Point
```

## VScode Extensions

This is a list of extensions that this project was configured to work with. It has only been tested on VScode.

**Extensions:**
- [Black Formatter](https://marketplace.visualstudio.com/items?itemName=ms-python.black-formatter)
- [Mypy Type Checker](https://marketplace.visualstudio.com/items?itemName=ms-python.mypy-type-checker)
- [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance)
- [Python Debugger](https://marketplace.visualstudio.com/items?itemName=ms-python.debugpy)
- [Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff)

### Black Formatter

You can configure Black to format on save (`Ctrl`+`S`) with the following configuration in **Preferences: Open User Settings (JSON)** (`Ctrl`+`Shift`+`P`).

```
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true
  }
```

## Workflows

### `tests.yml`

This workflow runs an identical set of checks that the `.pre-commit-config.yaml` runs. This means that if you were able to commit you should pass this workflow.

### `check_pr_labels.yml`

This workflow checks if you correctly labeled your PR for the `release.yml` workflow to create a proper release. *This workflow will recheck when new labels are added to the PR.*

**Setup:** To setup this workflow, you just need a `CONTRIBUTING.md` file in the root of your project. At minimum it should have a section called `No semver label!` ([Link to example](https://github.com/alexchristy/PyOPN/blob/main/CONTRIBUTING.md#no-semver-label)). The workflow will automatically link this section when it fails so user's can fix their PRs. Feel free to copy the example.

### `release.yml`

This workflow automatically creates GitHub tagged releases based on the tag of the PR. 

**Setup:**

1) Install the [Auto release tool](https://intuit.github.io/auto/docs) ([Latest release](https://github.com/intuit/auto/releases))

2) Navigate to the repository

    ```bash
    cd /path/to/repo/API/
    ```

3) Initialize Auto

    For this step the choose `Git Tag` as the *package manager plugin*. Fill in the rest of the information relevant to the repo and keep **all** default values. 

    When prompted for a *Github PAT*, go to the next step.

    ```bash
    auto init
    ```

4) Create repository tags

    This will allow you to tag your PRs and control the semantic version changes.

    ```bash
    auto create-labels
    ```

5) Create a GitHub App

    ***Note:** OpenLabsX already has the `auto-release-app` installed. Skip to step 7.*

    This allows us to enforce branch protection rules while allowing the Auto release tool to bypass the protections when running automated workflows. (Source: [Comment Link](https://github.com/orgs/community/discussions/13836#discussioncomment-8535364))
    
    Link: [Making authenticated API requests with a GitHub App in a GitHub Actions workflow](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/making-authenticated-api-requests-with-a-github-app-in-a-github-actions-workflow)

6) Configure the app with the following permissions

    * Actions (read/write)
    * Administration (read/write)
    * Contents (read/write)

7) Update the ruleset bypass list to include the GitHub App

8) Add GitHub app variables and secrets

    **Secrets:**
    * `AUTO_RELEASE_APP_PRIVATE_KEY`
    * `AUTO_RELEASE_APP_ID`