# GitHub Actions Workflow for PyPI Deployment

This directory contains the GitHub Actions workflow for automatically testing and deploying the `physicell-settings` package to PyPI.

## Workflow: `publish-to-pypi.yml`

### Trigger
The workflow is triggered when you push a version tag to the repository:
```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

Tags must match the pattern `v*` (e.g., `v1.0.0`, `v0.5.0`, `v2.1.0-beta`).

### Workflow Jobs

The workflow consists of three sequential jobs:

#### 1. **Test** (`test`)
- **Purpose**: Verify the package can be installed and imported on all supported Python versions
- **Runs on**: Ubuntu Latest
- **Python versions tested**: 3.8, 3.9, 3.10, 3.11, 3.12
- **Steps**:
  1. Check out the repository
  2. Set up Python (matrix strategy for multiple versions)
  3. Install the package in editable mode
  4. Run the full `pytest` test suite across all supported Python versions

#### 2. **Build** (`build`)
- **Purpose**: Build distribution packages (source distribution and wheel)
- **Runs on**: Ubuntu Latest
- **Depends on**: `test` job must pass
- **Steps**:
  1. Check out the repository
  2. Set up Python 3.11
  3. Install build dependencies (`build` and `twine`)
  4. Build the package using `python -m build`
  5. Validate the distribution packages using `twine check`
  6. Upload artifacts for the publish job

#### 3. **Publish to PyPI** (`publish-to-pypi`)
- **Purpose**: Publish the package to PyPI
- **Runs on**: Ubuntu Latest
- **Depends on**: `build` job must pass
- **Steps**:
  1. Download the built distribution packages
  2. Publish to PyPI using the official PyPI publish action

### Prerequisites

Before the workflow can successfully publish to PyPI, you need to:

1. **Create a PyPI API Token**:
   - Go to https://pypi.org/manage/account/token/
   - Create a new API token with scope for your package
   - Copy the token (it starts with `pypi-`)

2. **Add the token as a GitHub Secret**:
   - Go to your repository on GitHub
   - Navigate to Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `PYPI_API_TOKEN`
   - Value: Paste your PyPI API token
   - Click "Add secret"

### Usage

To release a new version of the package:

1. **Update the version number** in `setup.py`:
   ```python
   version="X.Y.Z",
   ```

2. **Update the CHANGELOG.md** with release notes

3. **Commit your changes**:
   ```bash
   git add setup.py CHANGELOG.md
   git commit -m "chore: bump version to X.Y.Z"
   git push
   ```

4. **Create and push a version tag**:
   ```bash
   git tag -a vX.Y.Z -m "Release version X.Y.Z"
   git push origin vX.Y.Z
   ```

5. **Monitor the workflow**:
   - Go to the "Actions" tab in your GitHub repository
   - Watch the workflow progress through testing, building, and publishing
   - If all jobs pass, your package will be published to PyPI!

### Workflow Behavior

- ✅ **All tests must pass** before building
- ✅ **Build must succeed** before publishing
- ✅ **Tests run on all supported Python versions** (3.8-3.12)
- ✅ **Automatic deployment** once a tag is pushed
- ⚠️ **Only triggered by tags** (not by regular commits)

### Troubleshooting

**Workflow doesn't trigger:**
- Ensure you pushed a tag (not just created it locally)
- Verify the tag matches the pattern `v*`

**Tests fail:**
- Check the test logs in the Actions tab
- Ensure the package can be imported: `python -c "import physicell_config"`
- Verify all dependencies are correctly specified in `setup.py`

**Build fails:**
- Check that `setup.py` and `pyproject.toml` are correctly configured
- Ensure all required files are included in the repository

**Publish fails:**
- Verify `PYPI_API_TOKEN` secret is correctly set
- Ensure the version number in `setup.py` hasn't been published before
- Check that your PyPI token has the correct permissions

### Security Notes

- The workflow uses API token authentication for PyPI publishing
- Never commit your PyPI API token to the repository
- Always use GitHub Secrets for sensitive credentials
- The token is only accessible during the publish job and is not exposed in logs

### Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [PyPI Publishing Guide](https://packaging.python.org/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
- [Trusted Publishers on PyPI](https://docs.pypi.org/trusted-publishers/)
