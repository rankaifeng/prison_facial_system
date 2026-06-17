import os
from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'

    def ready(self):
        if os.environ.get('RUN_MAIN') != 'false':
            from apps.users.services.dahua_event_service import DahuaEventService
            DahuaEventService.start()
