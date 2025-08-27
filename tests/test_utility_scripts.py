"""Tests for django_setup_tools utility scripts."""
import os
from unittest import TestCase
from unittest.mock import Mock, patch

from django.test import override_settings

from django_setup_tools.scripts import (
    check_database_connection,
    check_static_files_config,
    clear_cache,
    setup_log_directories,
    verify_environment_config,
)


class TestUtilityScripts(TestCase):
    """Test cases for utility scripts."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_handler = Mock()
        self.mock_handler.stdout = Mock()
        self.mock_handler.style = Mock()
        self.mock_handler.style.HTTP_INFO.return_value = "HTTP_INFO"
        self.mock_handler.style.SUCCESS.return_value = "SUCCESS"
        self.mock_handler.style.ERROR.return_value = "ERROR"
        self.mock_handler.style.WARNING.return_value = "WARNING"

    @patch('django_setup_tools.scripts.cache')
    def test_clear_cache_success(self, mock_cache):
        """Test successful cache clearing."""
        mock_cache.clear.return_value = None

        clear_cache(self.mock_handler)

        mock_cache.clear.assert_called_once()
        self.mock_handler.stdout.write.assert_any_call("HTTP_INFO")
        self.mock_handler.stdout.write.assert_any_call("SUCCESS")

    @patch('django_setup_tools.scripts.cache')
    def test_clear_cache_error(self, mock_cache):
        """Test cache clearing with error."""
        mock_cache.clear.side_effect = Exception("Cache error")

        clear_cache(self.mock_handler)

        self.mock_handler.stdout.write.assert_any_call("ERROR")

    @patch('django_setup_tools.scripts.connection')
    @override_settings(DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3'}})
    def test_check_database_connection_success(self, mock_connection):
        """Test successful database connection check."""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (1,)
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.vendor = "sqlite"

        check_database_connection(self.mock_handler)

        mock_cursor.execute.assert_called_with("SELECT 1")
        self.mock_handler.stdout.write.assert_any_call("SUCCESS")

    @patch('django_setup_tools.scripts.connection')
    def test_check_database_connection_error(self, mock_connection):
        """Test database connection check with error."""
        mock_connection.cursor.side_effect = Exception("Database error")

        check_database_connection(self.mock_handler)

        self.mock_handler.stdout.write.assert_any_call("ERROR")

    @patch('django_setup_tools.scripts.connection')
    @override_settings(DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3'}})
    def test_check_database_connection_failed_test(self, mock_connection):
        """Test database connection with failed result."""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None  # Failed result
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.vendor = "sqlite"

        check_database_connection(self.mock_handler)

        mock_cursor.execute.assert_called_with("SELECT 1")
        self.mock_handler.stdout.write.assert_any_call("ERROR")

    @override_settings(
        LOGGING={
            'handlers': {
                'file_handler': {
                    'filename': 'logs/test.log'  # nosec - test path
                },
                'console_handler': {
                    'class': 'logging.StreamHandler'
                }
            }
        }
    )
    @patch('django_setup_tools.scripts.Path')
    def test_setup_log_directories_mkdir_error(self, mock_path_class):
        """Test log directory setup with mkdir error."""
        mock_path = Mock()
        mock_path.parent = Mock()
        mock_path.parent.mkdir.side_effect = Exception("Permission denied")
        mock_path_class.return_value = mock_path

        setup_log_directories(self.mock_handler)

        self.mock_handler.stdout.write.assert_any_call("ERROR")

    @override_settings(
        LOGGING={
            'handlers': {
                'file_handler': {
                    'filename': 'logs/test.log'  # nosec - test path
                },
                'console_handler': {
                    'class': 'logging.StreamHandler'
                }
            }
        }
    )
    @patch('django_setup_tools.scripts.Path')
    def test_setup_log_directories_success(self, mock_path_class):
        """Test successful log directory setup."""
        mock_path = Mock()
        mock_path.parent = Mock()
        mock_path_class.return_value = mock_path

        setup_log_directories(self.mock_handler)

        mock_path.parent.mkdir.assert_called_with(parents=True, exist_ok=True)
        self.mock_handler.stdout.write.assert_any_call("SUCCESS")

    @override_settings(LOGGING={})
    def test_setup_log_directories_no_file_handlers(self):
        """Test log directory setup with no file handlers."""
        setup_log_directories(self.mock_handler)

        self.mock_handler.stdout.write.assert_any_call("WARNING")

    @override_settings(
        SECRET_KEY='test-secret-key-for-testing',  # nosec - test key
        DEBUG=True,
        ALLOWED_HOSTS=['localhost']
    )
    @patch.dict(os.environ, {'DATABASE_URL': 'postgres://test'})
    def test_verify_environment_config_success(self):
        """Test environment configuration verification with good config."""
        verify_environment_config(self.mock_handler)

        # Should report success for required settings and env vars
        self.mock_handler.stdout.write.assert_any_call("SUCCESS")

    @override_settings(SECRET_KEY='')
    @patch.dict(os.environ, {}, clear=True)
    def test_verify_environment_config_issues(self):
        """Test environment configuration verification with issues."""
        verify_environment_config(self.mock_handler)

        self.mock_handler.stdout.write.assert_any_call("ERROR")

    @override_settings(
        SECRET_KEY='test-secret-key-for-testing',  # nosec - test key
        DEBUG=True,
        ALLOWED_HOSTS=['localhost']
    )
    @patch.dict(os.environ, {'DATABASE_URL': 'postgres://test'})
    def test_verify_environment_config_warnings_only(self):
        """Test environment configuration with warnings but no errors."""
        # Clear one environment variable to trigger warning
        with patch.dict(os.environ, {'DATABASE_URL': ''}, clear=False):
            verify_environment_config(self.mock_handler)

        # Should show warnings but still indicate required config is present
        self.mock_handler.stdout.write.assert_any_call("SUCCESS")

    @override_settings(
        SECRET_KEY='test-secret-key-for-testing',  # nosec - test key
        DEBUG=True,
        ALLOWED_HOSTS=['localhost']
    )
    @patch.dict(os.environ, {
        'DATABASE_URL': 'postgres://test',
        'REDIS_URL': 'redis://test',
        'EMAIL_HOST': 'smtp.test.com'
    })
    def test_verify_environment_config_perfect(self):
        """Test environment configuration with no issues or warnings."""
        verify_environment_config(self.mock_handler)

        # Should show success for everything
        self.mock_handler.stdout.write.assert_any_call("SUCCESS")

    @override_settings(
        STATIC_URL='/static/',
        STATIC_ROOT='static_files',  # nosec - test path
        STATICFILES_DIRS=['app_static']  # nosec - test path
    )
    @patch('django_setup_tools.scripts.Path')
    def test_check_static_files_config_missing_directories(self, mock_path_class):
        """Test static files configuration with missing directories."""
        mock_path = Mock()
        mock_path.exists.return_value = False  # Directory doesn't exist
        mock_path_class.return_value = mock_path

        check_static_files_config(self.mock_handler)

        self.mock_handler.stdout.write.assert_any_call("ERROR")

    @override_settings(
        STATIC_URL='/static/',
        STATIC_ROOT='static_files',
        STATICFILES_DIRS=[('namespace', 'path/to/static')]  # Tuple format
    )
    @patch('django_setup_tools.scripts.Path')
    def test_check_static_files_config_tuple_format(self, mock_path_class):
        """Test static files configuration with tuple format STATICFILES_DIRS."""
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path_class.return_value = mock_path

        check_static_files_config(self.mock_handler)

        # Should handle tuple format: static_dir[1] for the path
        mock_path_class.assert_any_call('path/to/static')
        self.mock_handler.stdout.write.assert_any_call("SUCCESS")

    @override_settings(
        STATIC_URL='/static/',
        STATIC_ROOT='static_files',  # nosec - test path
        STATICFILES_DIRS=['app_static']  # nosec - test path
    )
    @patch('django_setup_tools.scripts.Path')
    def test_check_static_files_config_success(self, mock_path_class):
        """Test static files configuration check with good config."""
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path_class.return_value = mock_path

        check_static_files_config(self.mock_handler)

        self.mock_handler.stdout.write.assert_any_call("SUCCESS")

    @override_settings(STATIC_URL='', STATIC_ROOT='')
    def test_check_static_files_config_missing_settings(self):
        """Test static files configuration check with missing settings."""
        check_static_files_config(self.mock_handler)

        self.mock_handler.stdout.write.assert_any_call("ERROR")

    @patch('django_setup_tools.scripts.Site.objects.update_or_create')
    @override_settings(SITE_ID=1, SITE_DOMAIN='example.com', SITE_NAME='Test Site')
    def test_sync_site_id_database_error(self, mock_update_or_create):
        """Test sync_site_id with database error."""
        # Mock a database error
        mock_update_or_create.side_effect = Exception("Database connection failed")

        # This should raise an exception since we're not catching it in sync_site_id
        with self.assertRaises(Exception) as context:
            from django_setup_tools.scripts import sync_site_id
            sync_site_id(self.mock_handler)

        self.assertIn("Database connection failed", str(context.exception))

    def test_verify_environment_config_getattr_exception(self):
        """Test verify_environment_config with exception when checking settings."""
        # Mock getattr to raise an exception for a specific setting
        with patch('django_setup_tools.scripts.getattr') as mock_getattr:
            def side_effect(obj, name, default=None):
                if name == 'SECRET_KEY':
                    raise AttributeError("Mock error accessing SECRET_KEY")
                elif name == 'DEBUG':
                    return True
                elif name == 'DATABASES':
                    return {'default': {'ENGINE': 'django.db.backends.sqlite3'}}
                elif name == 'ALLOWED_HOSTS':
                    return ['localhost']
                elif name in ['MEDIA_ROOT', 'STATIC_ROOT']:
                    return '/test/path'  # nosec - test path
                return default

            mock_getattr.side_effect = side_effect
            verify_environment_config(self.mock_handler)

        # Check that the exception was handled
        self.mock_handler.stdout.write.assert_any_call("ERROR")

    @override_settings(
        STATIC_URL='/static/',
        STATIC_ROOT='/nonexistent/path',  # This should trigger the path check issue
        STATICFILES_DIRS=[]
    )
    @patch('django_setup_tools.scripts.Path')
    def test_check_static_files_config_path_evaluation_error(self, mock_path_class):
        """Test static files configuration with path evaluation error."""
        # Mock Path to raise an exception when trying to evaluate the path
        mock_path_class.side_effect = OSError("Permission denied or invalid path")

        # The function should raise the exception since it's not handled
        with self.assertRaises(OSError) as context:
            check_static_files_config(self.mock_handler)

        self.assertIn("Permission denied or invalid path", str(context.exception))
