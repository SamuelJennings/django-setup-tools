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
    return mocker.patch("django_setup_tools.management.commands.setup.MigrationRecorder", autospec=True)


@pytest.fixture
def custom_script(mocker):
    return mocker.patch("django_setup_tools.scripts.sync_site_id")


def test_db_intialization_no_env_set(django_settings, mock_migration_recorder, mock_call_command, custom_script):
    mock_migration_recorder.return_value.has_table.return_value = False

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


def test_db_intialization_development_env(django_settings, mock_migration_recorder, mock_call_command, custom_script):
    mock_migration_recorder.return_value.has_table.return_value = False  # Mock that the migration table DOES NOT exist

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


def test_db_already_intialized_no_env_set(django_settings, mock_migration_recorder, mock_call_command, custom_script):
    # Mock that the migration table DOES exist
    mock_migration_recorder.return_value.has_table.return_value = True

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
    django_settings, mock_migration_recorder, mock_call_command, custom_script
):
    # Mock that the migration table DOES exist
    mock_migration_recorder.return_value.has_table.return_value = True

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
