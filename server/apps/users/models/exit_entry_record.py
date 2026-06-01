from django.db import models


class ExitEntryRecord(models.Model):
    TYPE_CHOICES = [
        ('exit', '出监'),
        ('entry', '入监'),
    ]

    STATUS_CHOICES = [
        ('normal', '正常'),
        ('abnormal', '异常'),
    ]

    prisoner_no = models.CharField('罪犯编号', max_length=32)
    prisoner_name = models.CharField('罪犯姓名', max_length=64)
    prisoner_photo = models.CharField('罪犯照片', max_length=255, blank=True)
    prison_area = models.CharField('监区ID', max_length=32, blank=True)
    prison_area_name = models.CharField('监区名称', max_length=128, blank=True)
    type = models.CharField('类型', max_length=16, choices=TYPE_CHOICES)
    reason = models.CharField('出监原因', max_length=32, blank=True)
    exit_date = models.DateField('出监日期', null=True, blank=True)
    entry_date = models.DateField('入监日期', null=True, blank=True)
    police_face = models.CharField('民警人脸', max_length=255, blank=True)
    police_name = models.CharField('民警姓名', max_length=64, blank=True)
    swat_face = models.CharField('特警人脸', max_length=255, blank=True)
    swat_name = models.CharField('特警姓名', max_length=64, blank=True)
    armed_police_signature = models.TextField('武警签名', blank=True)
    armed_police_name = models.CharField('武警姓名', max_length=64, blank=True)
    hospital_type = models.CharField('医院类型', max_length=32, blank=True, null=True)
    hospital_name = models.CharField('医院名称', max_length=128, blank=True, null=True)
    operator_id = models.IntegerField('操作人ID', null=True)
    operator_name = models.CharField('操作人', max_length=64, blank=True)
    status = models.CharField('状态', max_length=16, default='processing')
    abnormal_reason = models.CharField('异常原因', max_length=255, blank=True)
    attachments = models.JSONField('附件', default=list, blank=True)
    start_time = models.CharField('开始时间', max_length=20, blank=True)
    end_time = models.CharField('结束时间', max_length=20, blank=True)
    video_url = models.CharField('录像存储URL', max_length=512, blank=True, null=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'exit_entry_record'
        ordering = ['-created_at']