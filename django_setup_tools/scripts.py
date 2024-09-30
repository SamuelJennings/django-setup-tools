from django.conf import settings
from django.contrib.sites.models import Site


def sync_site_id(handler, *args):
    handler.stdout.write(handler.style.HTTP_INFO("Synchronizing site object..."))

    site, created = Site.objects.update_or_create(
        id=settings.SITE_ID, defaults={"domain": settings.SITE_DOMAIN, "name": settings.SITE_NAME}
    )
    handler.stdout.write(f"Site: {site.name}")
    handler.stdout.write(f"Domain: {site.domain}")
