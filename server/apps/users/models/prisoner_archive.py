from django.db import models


class PrisonerArchive(models.Model):
    """罪犯档案表 - 存储从公安内网同步的罪犯基本信息和媒体信息"""

    # ========== 基本信息（常用字段单独建列，方便查询） ==========
    prisoner_no = models.CharField('罪犯编号', max_length=32, unique=True)
    prisoner_name = models.CharField('姓名', max_length=64, blank=True, default='')
    gender = models.CharField('性别', max_length=8, blank=True, default='')
    birth_date = models.CharField('出生日期', max_length=20, blank=True, default='')
    age = models.IntegerField('年龄', null=True, blank=True)
    id_card = models.CharField('身份证号', max_length=32, blank=True, default='')
    nation = models.CharField('民族', max_length=32, blank=True, default='')
    education = models.CharField('文化程度', max_length=32, blank=True, default='')
    marital_status = models.CharField('婚姻状况', max_length=16, blank=True, default='')
    native_place = models.CharField('籍贯', max_length=128, blank=True, default='')
    address = models.CharField('家庭地址', max_length=256, blank=True, default='')
    crime = models.CharField('罪名', max_length=128, blank=True, default='')
    sentence = models.CharField('原判刑期', max_length=64, blank=True, default='')
    sentence_start = models.CharField('刑期起日', max_length=20, blank=True, default='')
    sentence_end = models.CharField('刑期止日', max_length=20, blank=True, default='')
    prison_area = models.CharField('监区', max_length=64, blank=True, default='')
    room_no = models.CharField('监室号', max_length=32, blank=True, default='')
    bed_no = models.CharField('床号', max_length=32, blank=True, default='')
    status = models.CharField('在押状态', max_length=32, blank=True, default='')
    is_released = models.BooleanField('是否已释放', default=False, db_index=True)
    entry_date = models.CharField('入监日期', max_length=20, blank=True, default='')
    arrest_org = models.CharField('逮捕机关', max_length=128, blank=True, default='')
    judgment_org = models.CharField('判决机关', max_length=128, blank=True, default='')
    judgment_no = models.CharField('判决书号', max_length=128, blank=True, default='')

    # ========== 基础信息完整数据（JSON 存储所有字段，保留原始数据） ==========
    basic_info = models.JSONField('基础信息完整数据', default=dict, blank=True)

    # ========== 媒体信息 ==========
    media_info = models.JSONField('媒体信息列表', default=list, blank=True,
        help_text='每条包含: media_code, media_category, photo_path, remark')

    synced_at = models.DateTimeField('同步时间', auto_now=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'prisoner_archive'
        ordering = ['prisoner_no']
        verbose_name = '罪犯档案'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.prisoner_no} - {self.prisoner_name}'
