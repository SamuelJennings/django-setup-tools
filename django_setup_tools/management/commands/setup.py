from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder
from django.utils.module_loading import import_string


class Command(BaseCommand):
    def handle(self, *args, **options):
        # Get the environment, defaulting to "" if not set
        env = getattr(settings, "DJANGO_SETUP_TOOLS_ENV", "")

        # Get the setup tools configuration
        setup_tools = getattr(settings, "DJANGO_SETUP_TOOLS", {})

        self.stdout.write(self.style.NOTICE("Running initialization scripts (django_setup_tools):"))
        if not self.is_initialized():
            commands = self.get_commands(setup_tools, env, "on_initial")
            self.run_all(commands)
        else:
            self.stdout.write(self.style.HTTP_INFO("Database already initialized... skipping."))
        self.stdout.write(self.style.MIGRATE_HEADING("Running setup scripts (django_setup_tools):"))
        commands = self.get_commands(setup_tools, env, "always_run")
        self.run_all(commands)

    def is_initialized(self):
        return MigrationRecorder(connection).has_table()

    def get_commands(self, defaults, env, command_type):
        # Fetch the default on_initial scripts (under the "" key)
        commands = defaults.get("", {}).get(command_type, [])

        if env:
            # Append the environment-specific scripts
            commands += defaults.get(env, {}).get(command_type, [])

        return commands

    def run_all(self, commands: list):
        for command in commands:
            if isinstance(command, (list, tuple)):
                self.run_script(*command)
            else:
                self.run_script(command)

    def run_script(self, command, *args):
        if "." in command:
            # import func from module, then call it using args
            func = import_string(command)
            func(self, *args)
        else:
            # this is a management command
            call_command(command, *args)
