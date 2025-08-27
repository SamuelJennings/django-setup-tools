from unittest import mock

import pytest

from django_setup_tools.management.commands.setup import Command


@pytest.fixture
def django_settings(settings):
    settings.DJANGO_SETUP_TOOLS = {
        "": {
            "on_initial": [
                ("makemigrations", "--no-input"),
                ("migrate", "--no-input"),
                ("createsuperuser", "--no-input"),
            ],
            "always_run": [
                ("migrate", "--no-input"),
                "django_setup_tools.scripts.sync_site_id",
            ],
        },
        "development": {
            "on_initial": [
                ("loaddata", "on_initial_data"),
            ],
            "always_run": [
                ("loaddata", "always_run_data"),
            ],
        },
    }
    return settings


@pytest.fixture(scope="function")
def mock_call_command(mocker):
    return mocker.patch("django_setup_tools.management.commands.setup.call_command", autospec=True)


@pytest.fixture
def mock_import_string(mocker):
    return mocker.patch("django_setup_tools.management.commands.setup.import_string", autospec=True)


@pytest.fixture
def mock_migration_recorder(mocker):
    """Mock MigrationRecorder to avoid database dependencies."""
    mock_class = mocker.patch("django_setup_tools.management.commands.setup.MigrationRecorder")
    mock_instance = mock_class.return_value
    mock_instance.has_table.return_value = False  # Default: DB not initialized
    return mock_instance


@pytest.fixture
def mock_connection(mocker):
    """Mock database connection to avoid database dependencies."""
    mock_conn = mocker.patch("django_setup_tools.management.commands.setup.connection")
    # Make the connection appear healthy
    mock_conn.ensure_connection.return_value = None
    return mock_conn


@pytest.fixture
def custom_script(mocker):
    return mocker.patch("django_setup_tools.scripts.sync_site_id")


def test_db_intialization_no_env_set(django_settings, mock_migration_recorder, mock_connection, mock_call_command, custom_script):
    # Configure mock: database not yet initialized
    mock_migration_recorder.has_table.return_value = False

    Command().handle()

    # Test that the initial scripts were run
    mock_call_command.assert_any_call("makemigrations", "--no-input")
    mock_call_command.assert_any_call("migrate", "--no-input")
    mock_call_command.assert_any_call("createsuperuser", "--no-input")
    custom_script.assert_called_once_with(mock.ANY)

    # test the the env specific script was not run
    with pytest.raises(AssertionError):
        mock_call_command.assert_any_call("loaddata", "on_initial_data")

    # total number of calls to call_command
    assert mock_call_command.call_count == 4


def test_db_intialization_development_env(django_settings, mock_migration_recorder, mock_connection, mock_call_command, custom_script):
    # Configure mock: database not yet initialized
    mock_migration_recorder.has_table.return_value = False

    # Set the environment to development
    django_settings.DJANGO_SETUP_TOOLS_ENV = "development"  # Set the environment
    Command().handle()

    # Test that the initial scripts were run
    mock_call_command.assert_any_call("makemigrations", "--no-input")
    mock_call_command.assert_any_call("migrate", "--no-input")
    mock_call_command.assert_any_call("createsuperuser", "--no-input")
    custom_script.assert_called_once_with(mock.ANY)

    # test the the env specific script WAS run
    mock_call_command.assert_any_call("loaddata", "on_initial_data")

    # total number of calls to call_command
    assert mock_call_command.call_count == 6


def test_db_already_intialized_no_env_set(django_settings, mock_migration_recorder, mock_connection, mock_call_command, custom_script):
    # Configure mock: database already initialized
    mock_migration_recorder.has_table.return_value = True

    Command().handle()

    # Make sure that only the "always_run" scripts are run
    mock_call_command.assert_any_call("migrate", "--no-input")
    custom_script.assert_called_once_with(mock.ANY)

    # test that initialization scripts were not run
    with pytest.raises(AssertionError):
        mock_call_command.assert_any_call("makemigrations", "--no-input")

    # test that the env specific script was not run
    with pytest.raises(AssertionError):
        mock_call_command.assert_any_call("loaddata", "always_run_data")

    # total number of calls to call_command
    assert mock_call_command.call_count == 1


def test_db_already_intialized_development_env(
    django_settings, mock_migration_recorder, mock_connection, mock_call_command, custom_script
):
    # Configure mock: database already initialized
    mock_migration_recorder.has_table.return_value = True

    # Set the environment to development
    django_settings.DJANGO_SETUP_TOOLS_ENV = "development"  # Set the environment

    Command().handle()

    # Make sure that only the "always_run" scripts are run from the default config and the development config
    mock_call_command.assert_any_call("migrate", "--no-input")
    custom_script.assert_called_once_with(mock.ANY)

    # test that initialization scripts were not run
    with pytest.raises(AssertionError):
        mock_call_command.assert_any_call("makemigrations", "--no-input")

    # test that the env specific script WAS run
    mock_call_command.assert_any_call("loaddata", "always_run_data")

    # total number of calls to call_command
    assert mock_call_command.call_count == 2
