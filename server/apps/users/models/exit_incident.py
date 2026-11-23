from django.db import models


class ExitIncident(models.Model):
    exit_record = models.OneToOneField(
        'ExitEntryRecord', on_delete=models.CASCADE, related_name='exit_incident',
    )
    note = models.CharField(max_length=500)
    reporter_username = models.CharField(max_length=150)
    reported_at = models.DateTimeField(auto_now_add=True)
