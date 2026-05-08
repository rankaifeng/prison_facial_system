from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', '管理员'),
        ('operator', '操作员'),
        ('manager', '经理'),
    ]

    role = models.CharField('角色', max_length=32, choices=ROLE_CHOICES, default='operator')
    role_name = models.CharField('角色名称', max_length=64, blank=True)
    prison_id = models.CharField('所属监狱ID', max_length=32, blank=True)
    prison_name = models.CharField('所属监狱名称', max_length=128, blank=True)

    class Meta:
        db_table = 'user_login'
