from django.db import models


class HandheldSyncLog(models.Model):
    """手持终端同步记录 - 记录已同步的罪犯，用于增量同步"""

    prisoner_no = models.CharField('罪犯编号', max_length=64, unique=True, db_index=True)
    person_synced = models.BooleanField('人员已注册', default=False)
    photo_synced = models.BooleanField('照片已注册', default=False)
    synced_at = models.DateTimeField('最近同步时间', auto_now=True)

    class Meta:
        db_table = 'handheld_sync_log'
        verbose_name = '手持终端同步记录'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.prisoner_no} 人员={self.person_synced} 照片={self.photo_synced}'
