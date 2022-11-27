# Deploying

## Manual Deployments

Deploy your app or plugin to Steamship by running, respectively:

```bash
ship app:deploy
ship plugin:deploy
```

from the root directory of this project.

## Automated Deployments

This repository is configured to auto-deploy to Steamship when certain actions on GitHub occur.   

Production deployments occur upon:
* Pushes to `main`
* Pushes to any SemVer-style tag, prefixed with `v` (`vA.B.C`)

Staging deployments occur upon:
* Pushes to branch `staging`

When pushing to a SemVer-style tag, the tag's version must match the version contained within `steamship.json`.

New versions of a Steamship App or Plugin automatically become the "default" version. Unless an instance specifically requests a version, this default version will be used. 

## Deployment Setup

Automated deployments are parameterized by the following information:

* The `handle` property of `steamship.json`
* The `version` property of `steamship.json`
* The `STEAMSHIP_KEY` GitHub repository secret
* The `STEAMSHIP_API_BASE` GitHub repository secret (optional)
* The `STEAMSHIP_KEY_STAGING` GitHub repository secret
* The `STEAMSHIP_API_BASE_STAGING` GitHub repository secret (optional)

Setting the following variable will additionally trigger Slack notifications upon automated deployments:

* The `STEAMSHIP_SLACK_DEPLOYMENT_WEBHOOK` Slack notification webhook URL (optional)

## Staging setup

If you fork this repository and would like to establish your own staging workflow, we suggest the following workflow:

1. Creating a second Steamship account to act as your staging account. For example `acme_staging`, if your account is `acme`
2. Set the `STEAMSHIP_KEY_STAGING` GitHub secret to the API Key of that account
3. Leave the `STEAMSHIP_API_BASE_STAGING` GitHub secret blank; it will default to the appropriate API endpoint.

## Modifying or disabling automated deployments

Automated deployment is triggered by the GitHub Actions workflow in `.github/workflows/deploy.yml`. This file, in turn, invokes the `steamship-core/deploy-to-steamship@main` action.

To modify or disable automated deployments, remove, comment out, or modify that file.

## Troubleshooting

### The deployment fails because the version already exists

This means the version specified in `steamship.json` has already been registered with Steamship. Simply update the version in `steamship.json` to an identifier that has not yet been used.

### The deployment fails because the tag does not match the manifest file

This means you have tried to push a branch with a semver-style tag (like `v1.2.3`), resulting in a version deployment whose name must match that tag without the `v` prefix (`1.2.3`). Make sure the version field of `steamship.json` matches this string.

For example, if you are deploying branch `v6.0.0`, the `version` field of your `steamship.json` file must be `6.0.0`

### The deployment fails with an authentication error

Make sure you're set your `STEAMSHIP_KEY` in your GitHub secrets.