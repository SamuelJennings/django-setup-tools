"""Tests for django_setup_tools.management.commands.setup module."""
from unittest.mock import Mock, call, patch

import pytest
from django.core.management.base import CommandError
from django.test import override_settings

from django_setup_tools.management.commands.setup import Command


class TestSetupCommand:
    """Test cases for the setup management command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.command = Command()
        self.command.stdout = Mock()
        self.command.style = Mock()
        self.command.style.NOTICE.return_value = "NOTICE"
        self.command.style.HTTP_INFO.return_value = "HTTP_INFO"
        self.command.style.MIGRATE_HEADING.return_value = "MIGRATE_HEADING"
        self.command.style.WARNING.return_value = "WARNING"

    @override_settings(DJANGO_SETUP_TOOLS={})
    def test_handle_empty_configuration(self):
        """Test handle method with empty configuration."""
        self.command.handle()

        self.command.stdout.write.assert_any_call("WARNING")

    @override_settings(
        DJANGO_SETUP_TOOLS={
            "": {
                "on_initial": ["migrate"],
                "always_run": ["collectstatic"]
            }
        }
    )
    @patch('django_setup_tools.management.commands.setup.MigrationRecorder')
    @patch('django_setup_tools.management.commands.setup.call_command')
    def test_handle_first_run(self, mock_call_command, mock_migration_recorder):
        """Test handle method on first run (database not initialized)."""
        mock_migration_recorder.return_value.has_table.return_value = False

        self.command.handle()

        # Should run both initialization and always-run commands
        mock_call_command.assert_has_calls([
            call("migrate"),
            call("collectstatic")
        ])

    @override_settings(
        DJANGO_SETUP_TOOLS={
            "": {
                "on_initial": ["migrate"],
                "always_run": ["collectstatic"]
            }
        }
    )
    @patch('django_setup_tools.management.commands.setup.MigrationRecorder')
    @patch('django_setup_tools.management.commands.setup.call_command')
    def test_handle_subsequent_run(self, mock_call_command, mock_migration_recorder):
        """Test handle method on subsequent runs (database already initialized)."""
        mock_migration_recorder.return_value.has_table.return_value = True

        self.command.handle()

        # Should only run always-run commands
        mock_call_command.assert_called_once_with("collectstatic")

    @override_settings(
        DJANGO_SETUP_TOOLS_ENV="development",
        DJANGO_SETUP_TOOLS={
            "": {
                "on_initial": ["migrate"],
                "always_run": ["collectstatic"]
            },
            "development": {
                "on_initial": [("loaddata", "dev_fixtures")],
                "always_run": ["runserver"]
            }
        }
    )
    @patch('django_setup_tools.management.commands.setup.MigrationRecorder')
    @patch('django_setup_tools.management.commands.setup.call_command')
    def test_handle_with_environment(self, mock_call_command, mock_migration_recorder):
        """Test handle method with environment-specific configuration."""
        mock_migration_recorder.return_value.has_table.return_value = False

        self.command.handle()

        # Should run both default and environment-specific commands
        # Check that all expected commands were called
        mock_call_command.assert_any_call("migrate")  # default on_initial
        mock_call_command.assert_any_call("loaddata", "dev_fixtures")  # env on_initial
        mock_call_command.assert_any_call("collectstatic")  # default always_run
        mock_call_command.assert_any_call("runserver")  # env always_run

        # Verify the total number of calls
        assert mock_call_command.call_count == 4

    @patch('django_setup_tools.management.commands.setup.MigrationRecorder')
    def test_is_initialized_exception_handling(self, mock_migration_recorder):
        """Test is_initialized method handles exceptions gracefully."""
        mock_migration_recorder.return_value.has_table.side_effect = Exception("DB Error")

        result = self.command.is_initialized()

        assert result is True  # Should default to True for safety
        # Check that warning was written to stdout
        mock_call_args = self.command.stdout.write.call_args_list
        assert any("WARNING" in str(call) for call in mock_call_args)

    def test_get_commands_default_only(self):
        """Test get_commands method with default configuration only."""
        config = {
            "": {
                "on_initial": ["migrate", "createsuperuser"],
                "always_run": ["collectstatic"]
            }
        }

        commands = self.command.get_commands(config, "", "on_initial")
        assert commands == ["migrate", "createsuperuser"]

        commands = self.command.get_commands(config, "", "always_run")
        assert commands == ["collectstatic"]

    def test_get_commands_with_environment(self):
        """Test get_commands method with environment-specific configuration."""
        config = {
            "": {
                "on_initial": ["migrate"],
                "always_run": ["collectstatic"]
            },
            "production": {
                "on_initial": ["loaddata", "prod_fixtures"],
                "always_run": ["compress"]
            }
        }

        commands = self.command.get_commands(config, "production", "on_initial")
        assert commands == ["migrate", "loaddata", "prod_fixtures"]

        commands = self.command.get_commands(config, "production", "always_run")
        assert commands == ["collectstatic", "compress"]

    def test_get_commands_nonexistent_environment(self):
        """Test get_commands method with non-existent environment."""
        config = {
            "": {
                "on_initial": ["migrate"],
                "always_run": ["collectstatic"]
            }
        }

        commands = self.command.get_commands(config, "nonexistent", "on_initial")
        assert commands == ["migrate"]  # Should only return default commands

    @patch('django_setup_tools.management.commands.setup.call_command')
    def test_run_script_management_command(self, mock_call_command):
        """Test run_script method with Django management command."""
        self.command.run_script("migrate", "--fake")

        mock_call_command.assert_called_once_with("migrate", "--fake")

    @patch('django_setup_tools.management.commands.setup.import_string')
    def test_run_script_custom_function(self, mock_import_string):
        """Test run_script method with custom function."""
        mock_func = Mock()
        mock_import_string.return_value = mock_func

        self.command.run_script("myapp.scripts.my_function", "arg1", "arg2")

        mock_import_string.assert_called_once_with("myapp.scripts.my_function")
        mock_func.assert_called_once_with(self.command, "arg1", "arg2")

    @patch('django_setup_tools.management.commands.setup.import_string')
    def test_run_script_import_error(self, mock_import_string):
        """Test run_script method handles import errors."""
        mock_import_string.side_effect = ImportError("Module not found")

        with pytest.raises(CommandError, match="Could not import function"):
            self.command.run_script("nonexistent.function")

    @patch('django_setup_tools.management.commands.setup.call_command')
    def test_run_script_command_error(self, mock_call_command):
        """Test run_script method handles command execution errors."""
        mock_call_command.side_effect = Exception("Command failed")

        with pytest.raises(CommandError, match="Error executing management command"):
            self.command.run_script("badcommand")

    @patch('django_setup_tools.management.commands.setup.call_command')
    def test_run_all_single_commands(self, mock_call_command):
        """Test run_all method with single command strings."""
        commands = ["migrate", "collectstatic"]

        self.command.run_all(commands)

        expected_calls = [call("migrate"), call("collectstatic")]
        mock_call_command.assert_has_calls(expected_calls)

    @patch('django_setup_tools.management.commands.setup.call_command')
    def test_run_all_tuple_commands(self, mock_call_command):
        """Test run_all method with tuple commands."""
        commands = [("migrate", "--fake"), ["loaddata", "fixtures.json"]]

        self.command.run_all(commands)

        expected_calls = [
            call("migrate", "--fake"),
            call("loaddata", "fixtures.json")
        ]
        mock_call_command.assert_has_calls(expected_calls)

    @patch('django_setup_tools.management.commands.setup.call_command')
    def test_run_all_handles_errors(self, mock_call_command):
        """Test run_all method handles execution errors."""
        mock_call_command.side_effect = Exception("Command failed")
        commands = ["migrate"]

        with pytest.raises(CommandError, match="Failed to execute command"):
            self.command.run_all(commands)

    def test_run_all_empty_list(self):
        """Test run_all method with empty command list."""
        # Should not raise an error
        self.command.run_all([])

    @override_settings(
        DJANGO_SETUP_TOOLS={
            "": {
                "on_initial": [],
                "always_run": []
            }
        }
    )
    @patch('django_setup_tools.management.commands.setup.MigrationRecorder')
    def test_handle_empty_command_lists(self, mock_migration_recorder):
        """Test handle method with empty command lists."""
        mock_migration_recorder.return_value.has_table.return_value = False

        self.command.handle()

        # Should display appropriate messages for empty configurations
        self.command.stdout.write.assert_any_call("HTTP_INFO")

    @override_settings(
        DJANGO_SETUP_TOOLS={
            "": {
                "on_initial": ["django_setup_tools.scripts.sync_site_id"],
                "always_run": []
            }
        }
    )
    @patch('django_setup_tools.management.commands.setup.MigrationRecorder')
    @patch('django_setup_tools.management.commands.setup.import_string')
    def test_handle_custom_script_integration(self, mock_import_string, mock_migration_recorder):
        """Test handle method with custom script integration."""
        mock_migration_recorder.return_value.has_table.return_value = False
        mock_func = Mock()
        mock_import_string.return_value = mock_func

        self.command.handle()

        mock_import_string.assert_called_with("django_setup_tools.scripts.sync_site_id")
        mock_func.assert_called_once_with(self.command)
