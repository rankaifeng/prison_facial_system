from django.db import models


class TodayExitRecord(models.Model):
    prisoner_no = models.CharField('罪犯编号', max_length=32, unique=True)
    prisoner_name = models.CharField('罪犯姓名', max_length=64)
    prison_area = models.CharField('监区ID', max_length=32)
    prison_area_name = models.CharField('监区名称', max_length=128)
    exit_reason = models.CharField('出监原因', max_length=64)
    exit_date = models.DateTimeField('出监时间')

    class Meta:
        db_table = 'today_exit_records'
