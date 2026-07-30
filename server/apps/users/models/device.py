from django.db import models


class Device(models.Model):
    """人脸识别一体机设备"""

    device_no = models.CharField('设备编号', max_length=64, unique=True)
    name = models.CharField('设备名称', max_length=128, blank=True, default='')
    prison_area = models.CharField('所属监区', max_length=64, blank=True, default='')
    is_online = models.BooleanField('是否在线', default=False, db_index=True)
    last_seen_at = models.DateTimeField('最后心跳时间', null=True, blank=True)
    client_id = models.CharField('服务端分配的客户端ID', max_length=64, blank=True, default='')
    remark = models.CharField('备注', max_length=256, blank=True, default='')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'device'
        ordering = ['device_no']
        verbose_name = '一体机设备'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.device_no} - {self.name or "未命名"}'
