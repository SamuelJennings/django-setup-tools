# Django Setup Tools

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![Django Version](https://img.shields.io/badge/django-5.0%2B-green.svg)](https://djangoproject.com)
[![codecov](https://codecov.io/gh/SamuelJennings/django-setup-tools/branch/main/graph/badge.svg)](https://codecov.io/gh/SamuelJennings/django-setup-tools)
![GitHub](https://img.shields.io/github/license/SamuelJennings/django-setup-tools)
![GitHub last commit](https://img.shields.io/github/last-commit/SamuelJennings/django-setup-tools)

Django Setup Tools is a Django package that enables declarative configuration of setup scripts for Django applications. It provides a simple way to run initialization scripts and ongoing maintenance tasks in different environments during deployment.

## What It Does

Django Setup Tools allows you to:

- **Run initialization scripts** only when the database is first set up
- **Execute maintenance tasks** every time the setup command runs
- **Configure different behaviors** for different environments (development, staging, production)
- **Mix Django management commands** with custom Python functions
- **Ensure consistent deployment** across different environments

## Key Features

- 🚀 **Environment-specific configurations** - Different scripts for dev, staging, production
- 🔄 **One-time and recurring scripts** - Scripts that run only on initial setup vs. every deployment
- 🛠 **Flexible command types** - Support for Django management commands and custom Python functions
- 🎯 **Simple configuration** - Just add settings to your Django configuration
- 🧪 **Well-tested** - Comprehensive test suite with high coverage
- 📝 **Type-safe** - Full type hints for better IDE support

## Installation

### Using pip

```bash
pip install django-setup-tools
```

### Using Poetry

```bash
poetry add django-setup-tools
```

### Django Configuration

Add `django_setup_tools` to your `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    # ... your other apps
    'django_setup_tools',
]
```

## Quick Start

### 1. Basic Configuration

Add the setup configuration to your Django settings:

```python
# settings.py
DJANGO_SETUP_TOOLS = {
    "": {  # Default configuration (applies to all environments)
        "on_initial": [
            # These run only when the database is first initialized
            ("makemigrations", "--no-input"),
            ("migrate", "--no-input"),
            ("createsuperuser", "--no-input", "--username=admin", "--email=admin@example.com"),
        ],
        "always_run": [
            # These run every time the setup command is executed
            ("migrate", "--no-input"),
            "django_setup_tools.scripts.sync_site_id",  # Custom function
        ],
    }
}

# Required for sync_site_id script
SITE_ID = 1
SITE_DOMAIN = "your-domain.com"
SITE_NAME = "Your Site Name"
```

### 2. Run the Setup Command

```bash
python manage.py setup
```

This will:
- Check if the database is initialized
- Run `on_initial` scripts if it's the first time
- Always run `always_run` scripts

## Environment-Specific Configuration

You can configure different behaviors for different environments:

```python
# settings.py
DJANGO_SETUP_TOOLS_ENV = "development"  # or "staging", "production", etc.

DJANGO_SETUP_TOOLS = {
    "": {  # Default configuration
        "on_initial": [
            ("makemigrations", "--no-input"),
            ("migrate", "--no-input"),
        ],
        "always_run": [
            ("migrate", "--no-input"),
        ],
    },
    "development": {  # Development-specific
        "on_initial": [
            ("loaddata", "dev_fixtures.json"),
        ],
        "always_run": [
            ("collectstatic", "--no-input"),
        ],
    },
    "production": {  # Production-specific
        "on_initial": [
            ("createsuperuser", "--no-input", "--username=admin"),
        ],
        "always_run": [
            ("collectstatic", "--no-input"),
            ("compress", "--force"),
        ],
    },
}
```

## Command Types

### Django Management Commands

You can specify Django management commands in three formats:

```python
DJANGO_SETUP_TOOLS = {
    "": {
        "always_run": [
            "migrate",  # Simple command
            ("migrate", "--no-input"),  # Command with arguments (tuple)
            ["loaddata", "fixtures.json"],  # Command with arguments (list)
        ],
    }
}
```

### Custom Python Functions

You can also call custom Python functions:

```python
# myapp/scripts.py
def my_custom_setup(handler, *args):
    """Custom setup function."""
    handler.stdout.write("Running custom setup...")
    # Your custom logic here
    handler.stdout.write("Custom setup completed!")

# settings.py
DJANGO_SETUP_TOOLS = {
    "": {
        "always_run": [
            "myapp.scripts.my_custom_setup",
            ("myapp.scripts.my_custom_setup", "arg1", "arg2"),  # With arguments
        ],
    }
}
```

Custom functions receive:
- `handler`: The management command instance (for output and styling)
- `*args`: Any additional arguments specified in the configuration

## Built-in Scripts

Django Setup Tools includes many useful built-in scripts for common deployment and maintenance tasks:

### Site Management

#### sync_site_id

Synchronizes the Django Site object with your settings:

```python
# settings.py
SITE_ID = 1
SITE_DOMAIN = "yoursite.com"
SITE_NAME = "Your Site"

DJANGO_SETUP_TOOLS = {
    "": {
        "always_run": [
            "django_setup_tools.scripts.sync_site_id",
        ],
    }
}
```

### Cache Management

#### clear_cache

Clears all Django cache backends:

```python
DJANGO_SETUP_TOOLS = {
    "": {
        "always_run": [
            "django_setup_tools.scripts.clear_cache",
        ],
    }
}
```

### Database Health

#### check_database_connection

Verifies database connectivity and reports basic information:

```python
DJANGO_SETUP_TOOLS = {
    "": {
        "on_initial": [
            "django_setup_tools.scripts.check_database_connection",
        ],
    }
}
```

### User Management

Django provides built-in support for creating superusers from environment variables. Simply use Django's built-in `createsuperuser` command with the `--no-input` flag:

```bash
# Set environment variables
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_EMAIL=admin@yoursite.com
export DJANGO_SUPERUSER_PASSWORD=secure_password
```

```python
DJANGO_SETUP_TOOLS = {
    "": {
        "on_initial": [
            ("createsuperuser", "--no-input"),  # Uses environment variables automatically
        ],
    }
}
```

Django automatically looks for these environment variables:
- `DJANGO_SUPERUSER_USERNAME`
- `DJANGO_SUPERUSER_EMAIL`
- `DJANGO_SUPERUSER_PASSWORD`

### Configuration Validation

#### verify_environment_config

Checks for required environment variables and Django settings:

```python
DJANGO_SETUP_TOOLS = {
    "": {
        "always_run": [
            "django_setup_tools.scripts.verify_environment_config",
        ],
    }
}
```

#### check_static_files_config

Verifies static files configuration (STATIC_URL, STATIC_ROOT, etc.):

```python
DJANGO_SETUP_TOOLS = {
    "": {
        "on_initial": [
            "django_setup_tools.scripts.check_static_files_config",
        ],
    }
}
```

### Logging Setup

#### setup_log_directories

Creates log directories based on your Django logging configuration:

```python
DJANGO_SETUP_TOOLS = {
    "": {
        "on_initial": [
            "django_setup_tools.scripts.setup_log_directories",
        ],
    }
}
```

### Complete Example with Multiple Scripts

Here's a comprehensive example using multiple built-in scripts:

```python
DJANGO_SETUP_TOOLS = {
    "": {
        "on_initial": [
            "django_setup_tools.scripts.check_database_connection",
            "django_setup_tools.scripts.setup_log_directories",
            ("createsuperuser", "--no-input"),  # Uses environment variables automatically
            ("makemigrations", "--no-input"),
            ("migrate", "--no-input"),
            "django_setup_tools.scripts.sync_site_id",
        ],
        "always_run": [
            "django_setup_tools.scripts.verify_environment_config",
            "django_setup_tools.scripts.check_static_files_config",
            ("migrate", "--no-input"),
            ("collectstatic", "--no-input"),
            "django_setup_tools.scripts.clear_cache",
        ],
    }
}
```

## Advanced Usage

### Error Handling

The setup command will stop execution if any script fails. You can see detailed error messages in the output.

### Database Initialization Detection

The command automatically detects if the database has been initialized by checking for the Django migrations table. This ensures `on_initial` scripts only run once.

### Custom Script Best Practices

When writing custom scripts:

```python
def my_script(handler, *args):
    """
    Example custom script with best practices.

    Args:
        handler: Django management command instance
        *args: Additional arguments
    """
    # Use handler for output with proper styling
    handler.stdout.write(
        handler.style.NOTICE("Starting custom script...")
    )

    try:
        # Your logic here
        result = do_something()

        handler.stdout.write(
            handler.style.SUCCESS(f"Script completed: {result}")
        )
    except Exception as e:
        handler.stdout.write(
            handler.style.ERROR(f"Script failed: {e}")
        )
        raise  # Re-raise to stop execution
```

## Running Tests

### Install Development Dependencies

```bash
# Using Poetry
poetry install

# Or using pip
pip install -r requirements-dev.txt
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=django_setup_tools

# Run specific test file
pytest tests/test_setup_command.py

# Run with verbose output
pytest -v
```

### Test Structure

```
tests/
├── conftest.py                    # Pytest configuration
├── test_setup_command.py          # Original setup command tests
├── test_setup_command_extended.py # Extended setup command tests
├── test_scripts.py               # Tests for built-in scripts
└── test_integration.py           # Integration tests
```

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/your-username/django-setup-tools.git
cd django-setup-tools

# Install with Poetry
poetry install

# Or create virtual environment and install with pip
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
pip install -r requirements-dev.txt
```

### Code Quality

The project uses several tools for code quality:

```bash
# Format code
black .

# Check types
mypy src/

# Lint code
pylint src/

# Check imports
isort --check-only .

# Run all checks
tox
```

## Configuration Reference

### Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `DJANGO_SETUP_TOOLS` | dict | `{}` | Main configuration dictionary |
| `DJANGO_SETUP_TOOLS_ENV` | str | `""` | Environment name for environment-specific configs |
| `SITE_ID` | int | Required for sync_site_id | Django site ID |
| `SITE_DOMAIN` | str | Required for sync_site_id | Site domain name |
| `SITE_NAME` | str | Required for sync_site_id | Site display name |

### Configuration Structure

```python
DJANGO_SETUP_TOOLS = {
    "environment_name": {  # Use "" for default
        "on_initial": [
            # Commands that run only on first database initialization
        ],
        "always_run": [
            # Commands that run every time
        ],
    },
}
```

## Examples

### Development Environment

```python
# settings/development.py
DJANGO_SETUP_TOOLS_ENV = "development"

DJANGO_SETUP_TOOLS = {
    "": {
        "on_initial": [
            ("makemigrations", "--no-input"),
            ("migrate", "--no-input"),
        ],
        "always_run": [
            ("migrate", "--no-input"),
        ],
    },
    "development": {
        "on_initial": [
            ("loaddata", "dev_users.json"),
            ("loaddata", "dev_data.json"),
        ],
        "always_run": [
            "django_setup_tools.scripts.sync_site_id",
        ],
    },
}
```

### Production Environment

```python
# settings/production.py
DJANGO_SETUP_TOOLS_ENV = "production"

DJANGO_SETUP_TOOLS = {
    "": {
        "on_initial": [
            ("migrate", "--no-input"),
        ],
        "always_run": [
            ("migrate", "--no-input"),
        ],
    },
    "production": {
        "on_initial": [
            ("createsuperuser", "--no-input", "--username=admin"),
        ],
        "always_run": [
            ("collectstatic", "--no-input", "--clear"),
            ("compress", "--force"),
            "django_setup_tools.scripts.sync_site_id",
            "myapp.deployment.clear_cache",
        ],
    },
}
```

## Troubleshooting

### Common Issues

**Q: Scripts are running every time instead of just on initial setup**
A: Check that your database is properly configured and migrations table exists. The `on_initial` detection relies on Django's migration system.

**Q: Custom function not found**
A: Ensure the function path is correct and the module is importable. Use the full dotted path like `myapp.scripts.my_function`.

**Q: Commands failing with strange errors**
A: Check that all required Django apps are in `INSTALLED_APPS` and that the database is accessible.

### Debug Mode

Enable debug output by setting Django's logging level:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django_setup_tools': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Reporting Issues

Please report issues on [GitHub Issues](https://github.com/your-username/django-setup-tools/issues).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## Credits

- Created by Sam Jennings
- Inspired by the need for declarative Django deployment scripts
- Built with ❤️ for the Django community
