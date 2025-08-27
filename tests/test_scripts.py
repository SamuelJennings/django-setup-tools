"""Tests for django_setup_tools.scripts module."""
from unittest.mock import Mock, patch

import pytest
from django.core.management.base import BaseCommand
from django.test import override_settings

from django_setup_tools.scripts import sync_site_id


class TestSyncSiteId:
    """Test cases for sync_site_id function."""

    @override_settings(
        SITE_ID=1,
        SITE_DOMAIN="example.com",
        SITE_NAME="Example Site"
    )
    @patch('django_setup_tools.scripts.Site.objects.update_or_create')
    def test_sync_site_id_creates_new_site(self, mock_update_or_create):
        """Test that sync_site_id creates a new site when one doesn't exist."""
        # Arrange
        mock_site = Mock()
        mock_site.name = "Example Site"
        mock_site.domain = "example.com"
        mock_update_or_create.return_value = (mock_site, True)  # created=True

        mock_handler = Mock(spec=BaseCommand)
        mock_handler.stdout = Mock()
        mock_handler.style = Mock()
        mock_handler.style.HTTP_INFO.return_value = "info_style"

        # Act
        sync_site_id(mock_handler)

        # Assert
        mock_update_or_create.assert_called_once_with(
            id=1,
            defaults={
                "domain": "example.com",
                "name": "Example Site"
            }
        )
        mock_handler.stdout.write.assert_any_call("info_style")
        mock_handler.stdout.write.assert_any_call("Created site: Example Site")
        mock_handler.stdout.write.assert_any_call("Domain: example.com")

    @override_settings(
        SITE_ID=2,
        SITE_DOMAIN="updated.com",
        SITE_NAME="Updated Site"
    )
    @patch('django_setup_tools.scripts.Site.objects.update_or_create')
    def test_sync_site_id_updates_existing_site(self, mock_update_or_create):
        """Test that sync_site_id updates an existing site."""
        # Arrange
        mock_site = Mock()
        mock_site.name = "Updated Site"
        mock_site.domain = "updated.com"
        mock_update_or_create.return_value = (mock_site, False)  # created=False

        mock_handler = Mock(spec=BaseCommand)
        mock_handler.stdout = Mock()
        mock_handler.style = Mock()
        mock_handler.style.HTTP_INFO.return_value = "info_style"

        # Act
        sync_site_id(mock_handler)

        # Assert
        mock_update_or_create.assert_called_once_with(
            id=2,
            defaults={
                "domain": "updated.com",
                "name": "Updated Site"
            }
        )
        mock_handler.stdout.write.assert_any_call("Updated site: Updated Site")
        mock_handler.stdout.write.assert_any_call("Domain: updated.com")

    @override_settings(
        SITE_ID=1,
        SITE_DOMAIN="test.com",
        SITE_NAME="Test Site"
    )
    def test_sync_site_id_with_args(self):
        """Test that sync_site_id accepts additional arguments without error."""
        mock_handler = Mock(spec=BaseCommand)
        mock_handler.stdout = Mock()
        mock_handler.style = Mock()
        mock_handler.style.HTTP_INFO.return_value = "info_style"

        with patch('django_setup_tools.scripts.Site.objects.update_or_create') as mock_update_or_create:
            mock_site = Mock()
            mock_site.name = "Test Site"
            mock_site.domain = "test.com"
            mock_update_or_create.return_value = (mock_site, True)

            # This should not raise an error
            sync_site_id(mock_handler, "extra", "args")

            # Function should still work normally
            assert mock_update_or_create.called

    @override_settings(
        SITE_ID=1,
        SITE_DOMAIN="test.com",
        SITE_NAME="Test Site"
    )
    @patch('django_setup_tools.scripts.Site.objects.update_or_create')
    def test_sync_site_id_database_error(self, mock_update_or_create):
        """Test that sync_site_id handles database errors gracefully."""
        # Arrange
        mock_update_or_create.side_effect = Exception("Database error")
        mock_handler = Mock(spec=BaseCommand)
        mock_handler.stdout = Mock()
        mock_handler.style = Mock()
        mock_handler.style.HTTP_INFO.return_value = "info_style"

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            sync_site_id(mock_handler)

        # Verify the info message was still displayed
        mock_handler.stdout.write.assert_called_with("info_style")
