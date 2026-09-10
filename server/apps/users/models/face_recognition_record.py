from django.db import models


class FaceRecognitionRecord(models.Model):
    """一体机人脸识别记录（设备上报）"""

    device_no = models.CharField('设备编号', max_length=64, db_index=True)
    user_id = models.CharField('识别到的用户ID（罪犯编号）', max_length=64, blank=True, default='')
    prisoner = models.ForeignKey(
        'PrisonerArchive', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='recognition_records', verbose_name='关联的罪犯档案')
    captured_photo_url = models.CharField('现场抓拍照片URL', max_length=512, blank=True, default='')
    recognized_at = models.DateTimeField('识别时间', null=True, blank=True, db_index=True)
    raw_data = models.JSONField('原始上报数据', default=dict, blank=True)
    created_at = models.DateTimeField('记录时间', auto_now_add=True)

    class Meta:
        db_table = 'face_recognition_record'
        ordering = ['-recognized_at']
        verbose_name = '人脸识别记录'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.device_no} - {self.user_id or "未知"} - {self.recognized_at}'
