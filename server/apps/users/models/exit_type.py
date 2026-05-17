from django.db import models


class ExitType(models.Model):
    STATUS_CHOICES = [
        ('active', '启用'),
        ('disabled', '停用'),
    ]

    type_name = models.CharField('出监原因', max_length=128)
    parent = models.ForeignKey(
        'self',
        verbose_name='上级出监原因',
        null=True,
        blank=True,
        related_name='children',
        on_delete=models.CASCADE,
    )
    level = models.PositiveIntegerField('层级', default=1)
    sort_order = models.IntegerField('排序', default=0)
    status = models.CharField('状态', max_length=16, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'exit_type'
        ordering = ['sort_order', 'id']
        indexes = [
            models.Index(fields=['parent', 'sort_order', 'id']),
            models.Index(fields=['type_name']),
        ]
