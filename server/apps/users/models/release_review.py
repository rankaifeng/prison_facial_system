from django.db import models


class ReleaseReview(models.Model):
    class Decision(models.TextChoices):
        VERIFIED = 'verified', '身份已核对'
        NEEDS_REVIEW = 'needs_review', '疑似重复或资料存疑，待复核'

    archive = models.ForeignKey('PrisonerArchive', on_delete=models.CASCADE)
    release_date = models.DateField()
    decision = models.CharField(max_length=20, choices=Decision.choices)
    note = models.CharField(max_length=500, blank=True)
    reviewer_username = models.CharField(max_length=150)
    reviewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['release_date', 'archive'], name='unique_release_review'),
        ]
