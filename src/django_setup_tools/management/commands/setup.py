"""Django management command for running setup scripts."""
from typing import Any, Union

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder
from django.utils.module_loading import import_string

CommandSpec = Union[str, list[str], tuple[str, ...]]


class Command(BaseCommand):
    """
    Django management command for running environment-specific setup scripts.

    This command allows you to define setup scripts that run either:
    - on_initial: Only when the database is first initialized
    - always_run: Every time the command is executed

    Scripts can be environment-specific using DJANGO_SETUP_TOOLS_ENV setting.
    """

    help = "Run declarative setup scripts for Django deployment"

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute the setup command."""
        # Get the environment, defaulting to "" if not set
        env = getattr(settings, "DJANGO_SETUP_TOOLS_ENV", "")

        # Get the setup tools configuration
        setup_tools = getattr(settings, "DJANGO_SETUP_TOOLS", {})

        if not setup_tools:
            self.stdout.write(
                self.style.WARNING(
                    "No DJANGO_SETUP_TOOLS configuration found in settings."
                )
            )
            return

        self.stdout.write(
            self.style.NOTICE("Running initialization scripts (django_setup_tools):")
        )

        if not self.is_initialized():
            commands = self.get_commands(setup_tools, env, "on_initial")
            if commands:
                self.run_all(commands)
            else:
                self.stdout.write(
                    self.style.HTTP_INFO("No initialization scripts configured.")
                )
        else:
            self.stdout.write(
                self.style.HTTP_INFO("Database already initialized... skipping.")
            )

        self.stdout.write(
            self.style.MIGRATE_HEADING("Running setup scripts (django_setup_tools):")
        )
        commands = self.get_commands(setup_tools, env, "always_run")
        if commands:
            self.run_all(commands)
        else:
            self.stdout.write(self.style.HTTP_INFO("No always-run scripts configured."))

    def is_initialized(self) -> bool:
        """Check if the database has been initialized by looking for migration tables."""
        try:
            return MigrationRecorder(connection).has_table()
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(
                    f"Could not check database initialization status: {e}"
                )
            )
            return True  # Assume initialized to be safe

    def get_commands(
        self,
        defaults: dict[str, dict[str, list[CommandSpec]]],
        env: str,
        command_type: str,
    ) -> list[CommandSpec]:
        """
        Get commands for the specified environment and command type.

        Args:
            defaults: The setup tools configuration dictionary
            env: The current environment name
            command_type: Either "on_initial" or "always_run"

        Returns:
            List of command specifications to execute
        """
        # Fetch the default scripts (under the "" key)
        commands = defaults.get("", {}).get(command_type, [])

        if env and env in defaults:
            # Append the environment-specific scripts
            commands = commands + defaults.get(env, {}).get(command_type, [])

        return commands

    def run_all(self, commands: list[CommandSpec]) -> None:
        """
        Execute all commands in the list.

        Args:
            commands: List of command specifications to execute
        """
        for i, command in enumerate(commands, 1):
            self.stdout.write(f"Running script {i}/{len(commands)}...")
            try:
                if isinstance(command, list | tuple):
                    self.run_script(*command)
                else:
                    self.run_script(command)
            except Exception as e:
                msg = f"Failed to execute command {command}: {e}"
                raise CommandError(msg) from e

    def run_script(self, command: str, *args: str) -> None:
        """
        Execute a single script or management command.

        Args:
            command: The command to execute (either a dotted path to a function
                    or a Django management command name)
            *args: Arguments to pass to the command
        """
        if "." in command:
            # Import function from module, then call it using args
            try:
                func = import_string(command)
                self.stdout.write(f"Executing function: {command}")
                func(self, *args)
            except ImportError as e:
                msg = f"Could not import function '{command}': {e}"
                raise CommandError(msg) from e
            except Exception as e:
                msg = f"Error executing function '{command}': {e}"
                raise CommandError(msg) from e
        else:
            # This is a Django management command
            self.stdout.write(f"Executing management command: {command}")
            try:
                call_command(command, *args)
            except Exception as e:
                msg = f"Error executing management command '{command}': {e}"
                raise CommandError(msg) from e
