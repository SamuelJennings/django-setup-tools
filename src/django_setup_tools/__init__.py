"""
Django Setup Tools.

A Django package for declaratively configuring setup scripts that run
during deployment. Supports environment-specific configurations and
both one-time initialization and always-run scripts.
"""

__version__ = "0.1.0"
__author__ = "Sam Jennings"

default_app_config = "django_setup_tools.apps.DjangoSetupToolsConfig"
