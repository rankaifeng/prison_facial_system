from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_add_abnormal_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='exitentryrecord',
            name='start_time',
            field=models.CharField(blank=True, max_length=20, verbose_name='开始时间'),
        ),
        migrations.AddField(
            model_name='exitentryrecord',
            name='end_time',
            field=models.CharField(blank=True, max_length=20, verbose_name='结束时间'),
        ),
    ]