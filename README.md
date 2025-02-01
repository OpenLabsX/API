# API

## Developer Quickstart

1) Create virtual environment ([Python Download Link](https://www.python.org/downloads/))

    ```bash
    python3.12 -m venv venv
    ```

2) Activate virtual environment

    ```bash
    source venv/bin/activate
    ```

3) Instal dependencies

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

4) Create the GitHub PAT ([Link](https://github.com/settings/tokens/new))

    Select all `repo` (should have 5 sub permissions) and `workflow` (should only be one) permissions. If this is too permissive for you feel free to tweak the permissions at your own risk.

5) Configure `RELEASE_TOKEN` repository secret

    Navigate to your repo. Then click `Settings > Secrets and variables > Actions > New repository secret`. 

    Name it `RELEASE_TOKEN` and paste in the new GitHub PAT your generated in the previous step.
