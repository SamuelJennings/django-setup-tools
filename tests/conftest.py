"""Test configuration for django_setup_tools tests."""
import pytest
from django.conf import settings


def pytest_configure():
    """Configure Django settings for pytest."""
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            SECRET_KEY='test-secret-key-for-django-setup-tools',
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'django.contrib.sites',
                'django_setup_tools',
            ],
            SITE_ID=1,
            SITE_DOMAIN='test.example.com',
            SITE_NAME='Test Site',
            USE_TZ=True,
        )

    # Initialize Django
    import django
    django.setup()


@pytest.fixture
def django_db_setup():
    """Set up test database."""
    pass  # Use default Django test database setup


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Allow database access for all tests."""
    pass
