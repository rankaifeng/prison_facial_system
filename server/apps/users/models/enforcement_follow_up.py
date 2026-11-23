from django.db import models


class EnforcementFollowUp(models.Model):
    exit_record = models.OneToOneField(
        'ExitEntryRecord', on_delete=models.CASCADE, related_name='enforcement_follow_up',
    )
    note = models.CharField(max_length=500)
    operator_username = models.CharField(max_length=150)
    updated_at = models.DateTimeField(auto_now=True)
