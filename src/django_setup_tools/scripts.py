"""Built-in setup scripts for Django Setup Tools."""
import os
from pathlib import Path
from typing import Any

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db import connection


def sync_site_id(handler: BaseCommand, *args: Any) -> None:
    """
    Synchronize the site object with settings.

    Updates or creates a Site object with the ID specified in settings.SITE_ID,
    using domain and name from settings.SITE_DOMAIN and settings.SITE_NAME.

    Args:
        handler: The management command handler for output
        *args: Additional arguments (unused)
    """
    handler.stdout.write(handler.style.HTTP_INFO("Synchronizing site object..."))

    site, created = Site.objects.update_or_create(
        id=settings.SITE_ID,
        defaults={
            "domain": settings.SITE_DOMAIN,
            "name": settings.SITE_NAME
        }
    )

    action = "Created" if created else "Updated"
    handler.stdout.write(f"{action} site: {site.name}")
    handler.stdout.write(f"Domain: {site.domain}")


def clear_cache(handler: BaseCommand, *args: Any) -> None:
    """
    Clear all Django cache backends.

    Clears the default cache and reports the action to the user.

    Args:
        handler: The management command handler for output
        *args: Additional arguments (unused)
    """
    handler.stdout.write(handler.style.HTTP_INFO("Clearing Django cache..."))

    try:
        cache.clear()
        handler.stdout.write(handler.style.SUCCESS("✓ Cache cleared successfully"))
    except Exception as e:
        handler.stdout.write(
            handler.style.ERROR(f"✗ Failed to clear cache: {e}")
        )


def check_database_connection(handler: BaseCommand, *args: Any) -> None:
    """
    Verify database connectivity and basic health.

    Tests the database connection and reports basic information.

    Args:
        handler: The management command handler for output
        *args: Additional arguments (unused)
    """
    handler.stdout.write(handler.style.HTTP_INFO("Checking database connection..."))

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

        if result and result[0] == 1:
            handler.stdout.write(handler.style.SUCCESS("✓ Database connection successful"))
            handler.stdout.write(f"Database: {connection.vendor}")
            handler.stdout.write(f"Engine: {settings.DATABASES['default']['ENGINE']}")
        else:
            handler.stdout.write(handler.style.ERROR("✗ Database connection test failed"))

    except Exception as e:
        handler.stdout.write(
            handler.style.ERROR(f"✗ Database connection error: {e}")
        )


def setup_log_directories(handler: BaseCommand, *args: Any) -> None:
    """
    Create and verify log directories exist.

    Creates log directories based on Django logging configuration and reports status.

    Args:
        handler: The management command handler for output
        *args: Additional arguments (unused)
    """
    handler.stdout.write(handler.style.HTTP_INFO("Setting up log directories..."))

    logging_config = getattr(settings, 'LOGGING', {})
    handlers_config = logging_config.get('handlers', {})

    directories_created = []

    for _handler_name, handler_config in handlers_config.items():
        if 'filename' in handler_config:
            log_file_path = Path(handler_config['filename'])
            log_dir = log_file_path.parent

            try:
                log_dir.mkdir(parents=True, exist_ok=True)
                directories_created.append(str(log_dir))
                handler.stdout.write(f"✓ Ensured directory exists: {log_dir}")
            except Exception as e:
                handler.stdout.write(
                    handler.style.ERROR(f"✗ Failed to create log directory {log_dir}: {e}")
                )

    if not directories_created:
        handler.stdout.write(
            handler.style.WARNING("⚠ No file-based logging handlers found in configuration")
        )
    else:
        handler.stdout.write(
            handler.style.SUCCESS(f"✓ Log directory setup complete ({len(directories_created)} directories)")
        )


def verify_environment_config(handler: BaseCommand, *args: Any) -> None:
    """
    Check for required environment variables and settings.

    Verifies that essential configuration is present and reports any issues.

    Args:
        handler: The management command handler for output
        *args: Additional arguments (unused)
    """
    handler.stdout.write(handler.style.HTTP_INFO("Verifying environment configuration..."))

    # Common required settings
    required_settings = [
        ('SECRET_KEY', 'Django secret key'),
        ('DEBUG', 'Debug mode setting'),
        ('ALLOWED_HOSTS', 'Allowed hosts configuration'),
    ]

    # Optional but recommended environment variables
    recommended_env_vars = [
        ('DATABASE_URL', 'Database connection URL'),
        ('REDIS_URL', 'Redis connection URL'),
        ('EMAIL_HOST', 'Email host configuration'),
    ]

    issues = []
    warnings = []

    # Check required settings
    for setting_name, description in required_settings:
        try:
            value = getattr(settings, setting_name, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                issues.append(f"Missing or empty {setting_name} ({description})")
            else:
                handler.stdout.write(f"✓ {setting_name}: configured")
        except Exception as e:
            issues.append(f"Error checking {setting_name}: {e}")

    # Check recommended environment variables
    for env_var, description in recommended_env_vars:
        if not os.getenv(env_var):
            warnings.append(f"Missing {env_var} ({description})")
        else:
            handler.stdout.write(f"✓ {env_var}: set")

    # Report results
    if issues:
        handler.stdout.write(handler.style.ERROR("✗ Configuration issues found:"))
        for issue in issues:
            handler.stdout.write(f"  - {issue}")

    if warnings:
        handler.stdout.write(handler.style.WARNING("⚠ Recommended configuration:"))
        for warning in warnings:
            handler.stdout.write(f"  - {warning}")

    if not issues and not warnings:
        handler.stdout.write(handler.style.SUCCESS("✓ Environment configuration looks good"))
    elif not issues:
        handler.stdout.write(handler.style.SUCCESS("✓ Required configuration is present"))


def check_static_files_config(handler: BaseCommand, *args: Any) -> None:
    """
    Verify static files configuration and accessibility.

    Checks STATIC_URL, STATIC_ROOT, and staticfiles configuration.

    Args:
        handler: The management command handler for output
        *args: Additional arguments (unused)
    """
    handler.stdout.write(handler.style.HTTP_INFO("Checking static files configuration..."))

    issues = []

    # Check STATIC_URL
    static_url = getattr(settings, 'STATIC_URL', None)
    if not static_url:
        issues.append("STATIC_URL is not configured")
    else:
        handler.stdout.write(f"✓ STATIC_URL: {static_url}")

    # Check STATIC_ROOT
    static_root = getattr(settings, 'STATIC_ROOT', None)
    if not static_root:
        issues.append("STATIC_ROOT is not configured")
    else:
        handler.stdout.write(f"✓ STATIC_ROOT: {static_root}")

        # Check if STATIC_ROOT directory exists
        static_path = Path(static_root)
        if static_path.exists():
            handler.stdout.write("✓ Static root directory exists")
        else:
            issues.append(f"Static root directory does not exist: {static_root}")

    # Check STATICFILES_DIRS
    staticfiles_dirs = getattr(settings, 'STATICFILES_DIRS', [])
    if staticfiles_dirs:
        handler.stdout.write(f"✓ STATICFILES_DIRS configured ({len(staticfiles_dirs)} directories)")
        for i, static_dir in enumerate(staticfiles_dirs):
            dir_path = Path(static_dir) if isinstance(static_dir, str) else Path(static_dir[1])
            if dir_path.exists():
                handler.stdout.write(f"  ✓ Directory {i+1}: {dir_path}")
            else:
                issues.append(f"Static files directory does not exist: {dir_path}")

    # Report results
    if issues:
        handler.stdout.write(handler.style.ERROR("✗ Static files configuration issues:"))
        for issue in issues:
            handler.stdout.write(f"  - {issue}")
    else:
        handler.stdout.write(handler.style.SUCCESS("✓ Static files configuration looks good"))
