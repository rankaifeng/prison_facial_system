from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0016_user_plain_password'),
    ]

    operations = [
        # 1. 新增 Device 模型
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('device_no', models.CharField(max_length=64, unique=True, verbose_name='设备编号')),
                ('name', models.CharField(blank=True, default='', max_length=128, verbose_name='设备名称')),
                ('prison_area', models.CharField(blank=True, default='', max_length=64, verbose_name='所属监区')),
                ('is_online', models.BooleanField(db_index=True, default=False, verbose_name='是否在线')),
                ('last_seen_at', models.DateTimeField(blank=True, null=True, verbose_name='最后心跳时间')),
                ('client_id', models.CharField(blank=True, default='', max_length=64, verbose_name='服务端分配的客户端ID')),
                ('remark', models.CharField(blank=True, default='', max_length=256, verbose_name='备注')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
            ],
            options={
                'db_table': 'device',
                'ordering': ['device_no'],
                'verbose_name': '一体机设备',
                'verbose_name_plural': '一体机设备',
            },
        ),
        # 2. 新增 DeviceSyncLog 模型
        migrations.CreateModel(
            name='DeviceSyncLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prisoner_no', models.CharField(db_index=True, max_length=32, verbose_name='罪犯编号')),
                ('sync_type', models.CharField(
                    choices=[('incremental', '增量同步'), ('full', '全量同步')],
                    default='incremental', max_length=16, verbose_name='同步类型')),
                ('status', models.CharField(
                    choices=[('pending', '等待回执'), ('success', '成功'), ('fail', '失败'),
                             ('timeout', '超时'), ('offline', '设备离线'), ('error', '异常')],
                    db_index=True, default='pending', max_length=16, verbose_name='状态')),
                ('error_code', models.CharField(blank=True, default='', max_length=32, verbose_name='错误码')),
                ('error_msg', models.CharField(blank=True, default='', max_length=512, verbose_name='错误信息')),
                ('photo_url', models.CharField(blank=True, default='', max_length=512, verbose_name='下发的照片URL')),
                ('synced_at', models.DateTimeField(auto_now_add=True, verbose_name='同步时间')),
                ('device', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name='sync_logs',
                    to='users.device', verbose_name='设备')),
            ],
            options={
                'db_table': 'device_sync_log',
                'ordering': ['-synced_at'],
                'verbose_name': '一体机同步日志',
                'verbose_name_plural': '一体机同步日志',
                'indexes': [
                    models.Index(fields=['device', 'prisoner_no', 'status'], name='idx_dev_prisoner_status'),
                ],
            },
        ),
        # 3. PrisonerArchive 加两个增量同步字段
        migrations.AddField(
            model_name='prisonerarchive',
            name='last_synced_to_terminal_photo_url',
            field=models.CharField(
                blank=True, default='', help_text='一体机增量同步用，与大华独立维护',
                max_length=512, verbose_name='上次同步到一体机的照片URL'),
        ),
        migrations.AddField(
            model_name='prisonerarchive',
            name='last_synced_to_terminal_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='上次同步到一体机时间'),
        ),
        # 4. 新增 FaceRecognitionRecord 模型（依赖 PrisonerArchive，放最后）
        migrations.CreateModel(
            name='FaceRecognitionRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('device_no', models.CharField(db_index=True, max_length=64, verbose_name='设备编号')),
                ('user_id', models.CharField(blank=True, default='', max_length=64, verbose_name='识别到的用户ID（罪犯编号）')),
                ('captured_photo_url', models.CharField(blank=True, default='', max_length=512, verbose_name='现场抓拍照片URL')),
                ('recognized_at', models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='识别时间')),
                ('raw_data', models.JSONField(blank=True, default=dict, verbose_name='原始上报数据')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='记录时间')),
                ('prisoner', models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='recognition_records', to='users.prisonerarchive', verbose_name='关联的罪犯档案')),
            ],
            options={
                'db_table': 'face_recognition_record',
                'ordering': ['-recognized_at'],
                'verbose_name': '人脸识别记录',
                'verbose_name_plural': '人脸识别记录',
            },
        ),
    ]
