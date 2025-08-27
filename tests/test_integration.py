"""Integration tests for django_setup_tools package."""
from unittest.mock import Mock, patch

import pytest
from django.apps import apps
from django.core.management import call_command
from django.test import override_settings

from django_setup_tools.apps import DjangoSetupToolsConfig


def test_app_config():
    """Test that the app configuration is properly set up."""
    app_config = apps.get_app_config('django_setup_tools')
    assert isinstance(app_config, DjangoSetupToolsConfig)
    assert app_config.name == "django_setup_tools"


@override_settings(
    DJANGO_SETUP_TOOLS={
        "": {
            "on_initial": [],
            "always_run": ["check"]  # Use 'check' command which always exists
        }
    }
)
def test_setup_command_exists_and_runs():
    """Test that the setup command exists and can be executed."""
    # This should not raise an exception
    with patch('sys.stdout'):
        call_command('setup')


@override_settings(
    DJANGO_SETUP_TOOLS={
        "": {
            "on_initial": ["check"],
            "always_run": ["check"]
        }
    }
)
@patch('django_setup_tools.management.commands.setup.MigrationRecorder')
def test_setup_command_with_real_commands(mock_migration_recorder):
    """Test setup command with real Django commands."""
    # Mock that database is not initialized
    mock_migration_recorder.return_value.has_table.return_value = False

    # This should execute both on_initial and always_run commands
    with patch('sys.stdout'):
        call_command('setup')


def test_package_version():
    """Test that package version is accessible."""
    from django_setup_tools import __version__
    assert isinstance(__version__, str)
    assert len(__version__) > 0


class TestEnvironmentVariableHandling:
    """Test handling of environment variables."""

    @override_settings(
        DJANGO_SETUP_TOOLS_ENV="testing",
        DJANGO_SETUP_TOOLS={
            "": {
                "always_run": ["check"]
            },
            "testing": {
                "always_run": [("check", "--deploy")]  # Use tuple format for command with args
            }
        }
    )
    def test_environment_specific_commands(self, db):
        """Test that environment-specific commands are executed."""
        with patch('sys.stdout'):
            call_command('setup')

    @override_settings(
        DJANGO_SETUP_TOOLS={
            "": {
                "always_run": ["check"]
            }
        }
    )
    def test_no_environment_set(self, db):
        """Test behavior when no environment is explicitly set."""
        # Should work with default configuration
        with patch('sys.stdout'):
            call_command('setup')


class TestErrorHandling:
    """Test error handling scenarios."""

    @override_settings(
        DJANGO_SETUP_TOOLS={
            "": {
                "always_run": ["nonexistent_command"]
            }
        }
    )
    def test_invalid_management_command(self, db):
        """Test handling of invalid management commands."""
        from django.core.management.base import CommandError

        with pytest.raises(CommandError):
            call_command('setup')

    @override_settings(
        DJANGO_SETUP_TOOLS={
            "": {
                "always_run": ["nonexistent.module.function"]
            }
        }
    )
    def test_invalid_custom_function(self, db):
        """Test handling of invalid custom functions."""
        from django.core.management.base import CommandError

        with pytest.raises(CommandError):
            call_command('setup')

    @override_settings()
    def test_no_setup_tools_configuration(self, db):
        """Test behavior when DJANGO_SETUP_TOOLS is not configured."""
        # Should complete without error but show warning
        with patch('sys.stdout'):
            call_command('setup')


class TestCustomScriptExecution:
    """Test execution of custom scripts."""

    @override_settings(
        SITE_ID=1,
        SITE_DOMAIN="test.example.com",
        SITE_NAME="Test Site",
        DJANGO_SETUP_TOOLS={
            "": {
                "always_run": ["django_setup_tools.scripts.sync_site_id"]
            }
        }
    )
    @patch('django_setup_tools.scripts.Site.objects.update_or_create')
    def test_sync_site_id_execution(self, mock_update_or_create, db):
        """Test that sync_site_id script executes correctly."""
        mock_site = Mock()
        mock_site.name = "Test Site"
        mock_site.domain = "test.example.com"
        mock_update_or_create.return_value = (mock_site, True)

        with patch('sys.stdout'):
            call_command('setup')

        mock_update_or_create.assert_called_once_with(
            id=1,
            defaults={
                "domain": "test.example.com",
                "name": "Test Site"
            }
        )


class TestConfigurationValidation:
    """Test configuration validation and edge cases."""

    @override_settings(
        DJANGO_SETUP_TOOLS={
            "": {
                "on_initial": [
                    "check",  # single command
                    ["check", "--deploy"],  # command with args as list
                    ("check", "--deploy")  # command with args as tuple - use check instead of migrate
                ],
                "always_run": []
            }
        }
    )
    @patch('django_setup_tools.management.commands.setup.MigrationRecorder')
    def test_mixed_command_formats(self, mock_migration_recorder, db):
        """Test that different command formats work correctly."""
        mock_migration_recorder.return_value.has_table.return_value = False

        with patch('sys.stdout'):
            call_command('setup')

    @override_settings(
        DJANGO_SETUP_TOOLS={
            "production": {  # Only environment-specific, no default
                "always_run": ["check"]
            }
        },
        DJANGO_SETUP_TOOLS_ENV="production"
    )
    def test_environment_only_configuration(self, db):
        """Test configuration with only environment-specific settings."""
        with patch('sys.stdout'):
            call_command('setup')

    @override_settings(
        DJANGO_SETUP_TOOLS={
            "": {
                "on_initial": ["check"]
            }
            # No always_run section
        }
    )
    @patch('django_setup_tools.management.commands.setup.MigrationRecorder')
    def test_missing_always_run_section(self, mock_migration_recorder, db):
        """Test configuration missing always_run section."""
        mock_migration_recorder.return_value.has_table.return_value = False

        with patch('sys.stdout'):
            call_command('setup')
