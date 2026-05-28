from django.db import models


class DailyStatistics(models.Model):
    prison_area = models.CharField('监区ID', max_length=32)
    prison_area_name = models.CharField('监区名称', max_length=128)
    date = models.DateField('统计日期')
    exit_count = models.IntegerField('出监总人数', default=0)
    entry_count = models.IntegerField('入监总人数', default=0)
    in_prison_count = models.IntegerField('实时在监人数', default=0)
    work_count = models.IntegerField('出工人数', default=0)
    reason_stats = models.JSONField('出监原因统计', default=dict)  # {"假释": 2, "外出就医": 1, ...}
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'daily_statistics'
        unique_together = ['prison_area', 'date']