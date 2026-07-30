from django.db import models


class DeviceSyncLog(models.Model):
    """一体机人员下发同步日志"""

    SYNC_TYPE_CHOICES = [
        ('incremental', '增量同步'),
        ('full', '全量同步'),
    ]
    STATUS_CHOICES = [
        ('pending', '等待回执'),
        ('success', '成功'),
        ('fail', '失败'),
        ('timeout', '超时'),
        ('offline', '设备离线'),
        ('error', '异常'),
    ]

    device = models.ForeignKey(
        'Device', on_delete=models.CASCADE, related_name='sync_logs',
        verbose_name='设备')
    prisoner_no = models.CharField('罪犯编号', max_length=32, db_index=True)
    sync_type = models.CharField('同步类型', max_length=16, choices=SYNC_TYPE_CHOICES, default='incremental')
    status = models.CharField('状态', max_length=16, choices=STATUS_CHOICES, default='pending', db_index=True)
    error_code = models.CharField('错误码', max_length=32, blank=True, default='')
    error_msg = models.CharField('错误信息', max_length=512, blank=True, default='')
    photo_url = models.CharField('下发的照片URL', max_length=512, blank=True, default='')
    synced_at = models.DateTimeField('同步时间', auto_now_add=True)

    class Meta:
        db_table = 'device_sync_log'
        ordering = ['-synced_at']
        verbose_name = '一体机同步日志'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['device', 'prisoner_no', 'status'], name='idx_dev_prisoner_status'),
        ]

    def __str__(self):
        return f'{self.device.device_no} - {self.prisoner_no} - {self.status}'
