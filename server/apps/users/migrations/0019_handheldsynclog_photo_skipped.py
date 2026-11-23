from django.db import migrations, models


def reset_photo_synced(apps, schema_editor):
    """一次性重置 photo_synced。
    历史版本会把"照片URL无效被跳过"的人误标为 photo_synced=True，导致档案照片
    补齐后永远不会再同步到手持终端。旧数据无法区分"真成功"和"被跳过"，
    统一重置后下次同步会重新推送全部照片（设备端覆盖注册，幂等），
    一次性修复所有漏同步的人。"""
    HandheldSyncLog = apps.get_model('users', 'HandheldSyncLog')
    HandheldSyncLog.objects.all().update(photo_synced=False)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0018_handheld_sync_log'),
    ]

    operations = [
        migrations.AddField(
            model_name='handheldsynclog',
            name='photo_skipped',
            field=models.BooleanField(default=False, verbose_name='照片曾被跳过(无有效照片)'),
        ),
        migrations.RunPython(reset_photo_synced, migrations.RunPython.noop),
    ]
