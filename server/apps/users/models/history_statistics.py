from django.db import models


class HistoryStatistics(models.Model):
    prison_area = models.CharField('监区ID', max_length=32)
    prison_area_name = models.CharField('监区名称', max_length=128)
    date = models.DateField('统计日期')
    exit_count = models.IntegerField('出监总人数', default=0)
    exit_reason_1 = models.IntegerField('刑满释放', default=0)
    exit_reason_2 = models.IntegerField('外出就医', default=0)
    exit_reason_3 = models.IntegerField('外出教育', default=0)
    exit_reason_4 = models.IntegerField('离监探亲', default=0)
    exit_reason_5 = models.IntegerField('押回重审', default=0)
    entry_count = models.IntegerField('入监总人数', default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'history_statistics'
        ordering = ['-date']