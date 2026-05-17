from django.db import models


class DailyStatistics(models.Model):
    prison_area = models.CharField('分监区ID', max_length=32)
    prison_area_name = models.CharField('分监区名称', max_length=128)
    date = models.DateField('统计日期')
    exit_count = models.IntegerField('出监总人数', default=0)
    exit_reason_1 = models.IntegerField('刑满释放', default=0)
    exit_reason_2 = models.IntegerField('外出就医', default=0)
    exit_reason_3 = models.IntegerField('外出教育', default=0)
    exit_reason_4 = models.IntegerField('离监探亲', default=0)
    exit_reason_5 = models.IntegerField('押回重审', default=0)
    entry_count = models.IntegerField('入监总人数', default=0)
    in_prison_count = models.IntegerField('实时在监人数', default=0)
    work_count = models.IntegerField('出工人数', default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'daily_statistics'
        unique_together = ['prison_area', 'date']