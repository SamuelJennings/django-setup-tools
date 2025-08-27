from invoke import task


@task
def install(c):
    """
    Install the project dependencies
    """
    print("🚀 Creating virtual environment using pyenv and poetry")
    c.run("poetry install")
    c.run("poetry run pre-commit install")
    c.run("poetry shell")


@task
def check(c):
    """
    Check the consistency of the project using various tools
    """
    print("🚀 Checking Poetry lock file consistency with 'pyproject.toml': Running poetry check --lock")
    c.run("poetry check --lock")

    print("🚀 Linting code: Running pre-commit")
    c.run("poetry run pre-commit run -a")

    print("🚀 Running manual pre-commit hooks (poetry-lock, poetry-export)")
    c.run("poetry run pre-commit run --hook-stage manual -a")

    print("🚀 Static type checking: Running mypy")
    c.run("poetry run mypy")

    print("🚀 Checking for obsolete dependencies: Running deptry")
    c.run("poetry run deptry .")


@task
def fmt(c):
    """
    Format code and update dependency files
    """
    print("🚀 Running code formatters")
    c.run("poetry run pre-commit run -a")

    print("🚀 Updating Poetry lock file")
    c.run("poetry lock --no-update")

    print("🚀 Updating requirements.txt")
    c.run("poetry export -o requirements.txt --with=dev --without-hashes")


@task
def test(c, tox=False):
    """
    Run the test suite
    """
    if tox:
        print("🚀 Testing code: Running pytest with all tests")
        c.run("tox")
    else:
        print("🚀 Testing code: Running pytest")
        c.run("poetry run pytest --cov --cov-config=pyproject.toml --cov-report=html")

@task
def prerelease(c):
    """
    Run comprehensive pre-release checks and update all required files.

    This task performs all necessary steps to prepare the repository for release:
    1. Run linting and formatting (including poetry-lock hook)
    2. Run all quality checks and tests
    3. Update requirements.txt

    Use this before running the release task to ensure everything is ready.
    """
    print("🚀 Starting comprehensive pre-release checks...")
    print("=" * 60)

    # Step 1: Run comprehensive linting and type checking (including poetry-lock)
    print("\n🧹 Step 1: Running comprehensive linting and type checking")
    print("🚀 Running pre-commit hooks")
    c.run("poetry run pre-commit run -a")

    print("🚀 Running manual pre-commit hooks (poetry-lock, poetry-export)")
    c.run("poetry run pre-commit run --hook-stage manual -a")

    # Step 2: Check Poetry lock file consistency
    print("\n🔍 Step 2: Checking Poetry lock file consistency")
    print("🚀 Checking Poetry lock file consistency with 'pyproject.toml'")
    c.run("poetry check --lock")

    print("🚀 Static type checking with mypy")
    c.run("poetry run mypy")

    print("🚀 Checking for obsolete dependencies with deptry")
    c.run("poetry run deptry .")

    # Step 3: Run comprehensive test suite
    print("\n🧪 Step 3: Running comprehensive test suite")
    print("🚀 Running pytest with coverage")
    c.run("poetry run pytest --cov --cov-config=pyproject.toml --cov-report=html")

    # Step 4: Update requirements.txt (final step)
    print("\n📦 Step 4: Updating requirements.txt")
    print("🚀 Exporting Poetry dependencies to requirements.txt")
    c.run("poetry export -o requirements.txt --with=dev --without-hashes")

    print("\n" + "=" * 60)
    print("✅ Pre-release checks completed successfully!")
    print("🎉 Repository is ready for release. You can now run 'invoke release' with the appropriate rule.")
    print("   Example: invoke release --rule=patch")


@task
def release(c, rule=""):
    """
    Create a new git tag and push it to the remote repository.

    .. note::
        This will create a new tag and push it to the remote repository, which will trigger a new build and deployment of the package to PyPI.

    RULE	    BEFORE	AFTER
    major	    1.3.0	2.0.0
    minor	    2.1.4	2.2.0
    patch	    4.1.1	4.1.2
    premajor	1.0.2	2.0.0a0
    preminor	1.0.2	1.1.0a0
    prepatch	1.0.2	1.0.3a0
    prerelease	1.0.2	1.0.3a0
    prerelease	1.0.3a0	1.0.3a1
    prerelease	1.0.3b0	1.0.3b1
    """
    if rule:
        # bump the current version using the specified rule
        c.run(f"poetry version {rule}")

    # 1. Get the current version number as a variable
    version_short = c.run("poetry version -s", hide=True).stdout.strip()
    version = c.run("poetry version", hide=True).stdout.strip()

    # 2. commit the changes to pyproject.toml
    c.run(f'git commit pyproject.toml -m "Release v{version_short}"')

    # 3. create a tag and push it to the remote repository
    c.run(f'git tag -a v{version_short} -m "{version}"')
    c.run("git push --tags")
    c.run("git push origin main")


@task
def live_docs(c):
    """
    Build the documentation and open it in a live browser
    """
    c.run("sphinx-autobuild -b html --host 0.0.0.0 --port 9000 --watch . -c . . _build/html")
