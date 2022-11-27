# Testing

## Manual Testing

Tests are located in the `test/` folder. You can run them with:

```bash
pytest
```

We have provided sample data in the `test_data/` folder. 

On your local machine, these tests will run using the `STEAMSHIP_API_KEY` environment variable, if available, or using the key specified in your user-global Steamship settings (`~/.steamship.json`).

## Automated testing

This repository is configured to auto-test upon pull-requests to the `main` and `staging` branches. Testing will also be performed as part of the automated deployment (see `DEPLOYING.md`)

* Failing tests are will block any automated deployments
* We recommend configuring your repository to block pull-request merges unless a passing test has been registered

### Automated testing setup

Testing requires that you set a GitHub secret named `steamship_key_test`. This secret will be used to set the `STEAMSHIP_API_KEY` environment variable during test running.

### Configuring or removing automated testing

Automated tests are run from the GitHub workflow located in `.github/workflows/test.yml`

