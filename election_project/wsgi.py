"""
WSGI config for election_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from whitenoise import WhiteNoise
from django.conf import settings
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'election_project.settings')

application = get_wsgi_application()

application = WhiteNoise(application, root=settings.MEDIA_ROOT, prefix=settings.MEDIA_URL)
