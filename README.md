# Streamlit Deploy - Guided Lab

This Hands-on Lab guides you through deploying a simple Streamlit app to Snowflake using GitHub Actions.

You will fork and start from a minimal `start` branch and build the app step-by-step, using tools such as `uv`, the Snowflake CLI, and GitHub Actions for automated deployment and testing.

The repository is intentionally structured to let you create the necessary files and configurations yourself. The `main` branch contains the full reference implementation for comparison.

> [!IMPORTANT]
> Streamlit in Snowflake is a great way to leverage the power of Snowflake's data platform with the simplicity of Streamlit for building data applications, however, this pattern is most suitable for POCs and demos.
> For production workloads, we recommend deploying Streamlit as a Native App.
> See [Next Steps](#next-steps) for more information on deploying Streamlit as a Native App.

## Getting Started

First, fork this repository to your own GitHub account so that you can configure Secrets and trigger Actions.

Click the "Fork" button at the top of this page, then clone your fork:

```bash
git clone https://github.com/YOUR-USERNAME/streamlit-deploy.git
```

Then open the repository in your terminal or IDE of choice.

## Requirements and Setup

- uv [installation instructions](https://docs.astral.sh/uv/getting-started/installation/)
- Python 3.8 or later (see below for installation instructions)
- Snowflake CLI [installation instructions](https://docs.snowflake.com/en/developer-guide/snowflake-cli/installation/installation)

If you don't have Python installed, follow the [uv Installing Python instructions](https://docs.astral.sh/uv/guides/install-python/) or run the following command to install the latest version of Python:

```bash
uv python install
```

Once you have Python installed, use `uv` to create a virtual environment and install the required packages:

```bash
uv sync
```

## Streamlit Deploy Lab

First, let's get a Streamlit app running and then we’ll deploy it using the [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index).

> [!NOTE]
> Many of these steps are possible with Snowflake SQL but the CLI minimizes that effort by avoiding manual steps like creating a stage and the application.

You can peruse the repo for the final setup, but we’ll walk through the steps to get there.

### Checkout the Start Branch

Before we start, let’s check out the `start` branch which contains minimal files leaving the work for you to complete:

```bash
git checkout start
```

If you get stuck along the way, you can always refer to the `main` branch which contains the completed code.

Your repository should only contain a few files at the root including this README.

### Create a Streamlit Application

The easiest way to start is by following the [Snowflake CLI - Creating a Streamlit app](https://docs.snowflake.com/en/developer-guide/snowflake-cli/streamlit-apps/manage-apps/initialize-app) docs.

To initialize your repository, use this command:

```bash
snow init src --template example_streamlit -D query_warehouse=mywarehouse -D stage=stage
```

Hit enter to accept any default values. It should create a directory structure like this:

```bash
(streamlit-deploy) ➜  streamlit-deploy git:(start) ✗ tree src
src
├── common
│   └── hello.py
├── environment.yml
├── pages
│   └── my_page.py
├── snowflake.yml
└── streamlit_app.py

3 directories, 5 files
```

At this point, you should be able to run the application locally:

```bash
uv run streamlit run src/streamlit_app.py
```

In your browser, you should see a simple Streamlit app open.

> [!NOTE]
> `uv run` commands are used to run Python scripts in the virtual environment created by `uv sync`. This ensures that the correct dependencies are used.

### Deploying to Snowflake Manually

Now, test deploying to your Snowflake account. [Snowflake currently supports Python 3.11 for Streamlit](https://docs.google.com/document/d/1_XGXT2rzBiWgo6b2PWT8oXmnjvITSRs1ak5Z92IQc-0/edit?tab=t.0) so ensure that is what you’re developing against.

> [!IMPORTANT]
> The following `snow` commands assume you have the Snowflake CLI installed and configured with a connection to your Snowflake account. If you have issues, check your `~/.snowflake/config.toml` file to ensure you have a connection set up.

To verify the app deploys correctly run:

```bash
snow streamlit deploy --project src
```

> [!TIP]
> Note the URL and navigate to it in your browser. You should see the same Streamlit app running as you did locally, but now hosted in Snowflake.

After verifying, you’re ready to set up GitHub Actions for deployment. First, tear down the app:

```bash
snow streamlit drop streamlit_app
```

### Testing the Streamlit Application

Before moving to Actions, let’s test the application.
Streamlit includes an [AppTest framework](https://docs.streamlit.io/develop/concepts/app-testing) to assert widgets, which can be run with pytest and easily integrated with a GitHub Action workflow.

To set up the tests, first create a directory and file for your tests:

```bash
mkdir src/tests
touch src/tests/test_streamlit_app.py
```

Then, add the following code to `src/tests/test_streamlit_app.py`:

```python
"""src/tests/test_streamlit_app.py"""

from streamlit.testing.v1 import AppTest


def test_title():
    at = AppTest.from_file("../streamlit_app.py").run()
    at.run()
    assert not at.exception
    assert at.title.values[0] == "Example streamlit app. Hello!"


def test_page():
    at = AppTest.from_file("../pages/my_page.py").run()
    at.run()
    assert not at.exception
    assert at.title.values[0] == "Example page"
```

Before you can run pytest, use uv to make sure it and other dev packages are installed:

```bash
uv add --dev pytest ruff
```

Now, run pytest in your terminal or IDE to ensure your tests pass:

```bash
uv run pytest
```

### Deploying with GitHub Actions

Now that we’ve validated our app locally, manually deployed to Snowflake, and tested, it’s time to automate deploying the Streamlit app to Snowflake with Actions. As we saw earlier, the Snowflake CLI makes this simple with snow streamlit deploy. Our Actions file will mimic the process we followed.

The file `.github/workflows/main.yml` checks out the code, installs dependencies, runs tests, configures a TOML file with a secret for Snowflake CLI authentication, and then deploys.

First, create the file `.github/workflows/main.yml` and add the following content:

```bash
mkdir -p .github/workflows
touch .github/workflows/main.yml
```

Then, copy the following content into the file:

```yaml
# .github/workflows/main.yml
name: Deploy via Snowflake CLI

on:
  push:
    branches:
      - main
  workflow_dispatch:
env:
  PYTHON_VERSION: "3.11"
  SNOWFLAKE_CLI_VERSION: "3.9.0"

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    environment: dev
    steps:
      - name: "Checkout GitHub Action"
        uses: actions/checkout@v4

      - name: Install uv
        shell: bash
        run: |
          curl -Ls https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-unknown-linux-gnu.tar.gz | tar -xz
          sudo mv uv /usr/local/bin/uv
          uv --version
        
      - name: Install Python
        shell: bash
        run: |
          uv python install ${{ env.PYTHON_VERSION }}
          uv run python --version

      - name: "Install Dependencies"
        shell: bash
        run: |
          uv sync

      - name: "Test"
        shell: bash
        run: |
          uv run pytest

      - name: "Create config"
        shell: bash
        run: |
          mkdir -p ~/.snowflake
          cp config.toml ~/.snowflake/config.toml
          chmod 0600 ~/.snowflake/config.toml

      - name: "Write private key"
        shell: bash
        env:
          PRIVATE_KEY_FILE_CONTENT: ${{ secrets.PRIVATE_KEY_FILE_CONTENT }}
        run: |
          printf "%s" "$PRIVATE_KEY_FILE_CONTENT" > rsa_key.p8
          chmod 0600 rsa_key.p8

      - uses: snowflakedb/snowflake-cli-action@v1.5
        with:
          cli-version: ${{ env.SNOWFLAKE_CLI_VERSION }}

      - name: "Deploy the Streamlit app"
        shell: bash
        env:
          SNOWFLAKE_CONNECTIONS_MYCONNECTION_ACCOUNT: ${{ secrets.SNOWFLAKE_ACCUNT }}
          SNOWFLAKE_CONNECTIONS_MYCONNECTION_USER: ${{ secrets.SNOWFLAKE_USER }}
          SNOWFLAKE_CONNECTIONS_MYCONNECTION_ROLE: ${{ secrets.SNOWFLAKE_ROLE }}
          SNOWFLAKE_CONNECTIONS_MYCONNECTION_WAREHOUSE: ${{ secrets.SNOWFLAKE_WAREHOUSE }}
          SNOWFLAKE_CONNECTIONS_MYCONNECTION_DATABASE: ${{ secrets.SNOWFLAKE_DATABASE }}
          PRIVATE_KEY_PASSPHRASE: ${{ secrets.PRIVATE_KEY_PASSPHRASE }}
        run: |
          snow streamlit deploy --replace
```

### Key Pair Authentication Setup

Before the Action can successfully deploy we need to enable key auth for our Snowflake user.

First, from the Snowflake Key Pair Auth docs run these commands to generate the key pairs:

```bash
openssl genrsa 2048 | openssl pkcs8 -topk8 -v2 des3 -inform PEM -out rsa_key.p8
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
```

While you have the passphrase, export a local variable that we'll use in a bit:

```bash
export PRIVATE_KEY_PASSPHRASE={{ the passphrase you provided }}
```

Finally, assign the public key to your Snowflake user:

```sql
ALTER USER myuser SET RSA_PUBLIC_KEY='MIIBIjANBgkqh...';
```

### Verify Key Pair Authentication

Verify auth with Snowflake CLI by running the command below in the directory where the newly created rsa_key.p8 file is within:

```bash
snow connection test --connection myconnection
```

Provide the passphrase you set earlier, and you should see a result similar to:

```plaintext
+--------------------------------------------------------------+
| key             | value                                      |
|-----------------+--------------------------------------------|
| Connection name | myconnection                    |
| Status          | OK                                         |
| Host            | myaccount.us-east-1.snowflakecomputing.com |
| Account         | myaccount                                  |
| User            | myuser                                     |
| Role            | accountadmin                               |
| Database        | MY_APP_PKG                                 |
| Warehouse       | mywarehouse                                |
+--------------------------------------------------------------+
```

> [!IMPORTANT]
> This command uses your local `~/.snowflake/config.toml` file to connect to your Snowflake account.
> Ensure the connection used to test contains the correct connection details, including the `authenticator` and `private_key_file` properties.
> See [Snowflake CLI - Use a private key file for authentication](https://docs.snowflake.com/en/developer-guide/snowflake-cli/connecting/configure-connections#use-a-private-key-file-for-authentication) for details.

### GitHub Secrets

The prior test used a local rsa_key.p8 file, but we need to ensure the Action can access the private key as well as information about your account without exposing that in with a commit to the config.toml.

To do this, set up the following GitHub Secrets in your repository:

- `PRIVATE_KEY_FILE_CONTENT`: The content of the `rsa_key.p8` file you generated earlier.
- `PRIVATE_KEY_PASSPHRASE`: The passphrase you set when generating the key pair.
- `SNOWFLAKE_ACCOUNT`: Your Snowflake account name (e.g., `myaccount`).
- `SNOWFLAKE_USER`: Your Snowflake user name (e.g., `myuser`).
- `SNOWFLAKE_ROLE`: The role you want to use for the deployment (e.g., `myrole`).
- `SNOWFLAKE_WAREHOUSE`: The warehouse you want to use for the deployment (e.g., `mywarehouse`).
- `SNOWFLAKE_DATABASE`: The database you want to use for the deployment (e.g., `mydatabase`).

> [!TIP]
> Get the values for those from your local `~/.snowflake/config.toml` file. See the [GitHub Secrets documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets) for how to set these up.

### Run the Streamlit Application

Merge your code to your main branch to trigger your Action to deploy the app. With the app deployed you can get the URL by looking at your GitHub Action log or with Snowflake CLI:

```bash
snow streamlit get-url streamlit_app
```

Navigate to that link to see the app run.

## Next Steps

Congratulations! You have successfully deployed a Streamlit in Snowflake app using GitHub Actions.

Proceed to the Streamlit Native App Deploy repo for a tutorial on how to deploy a Native App running Streamlit.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
