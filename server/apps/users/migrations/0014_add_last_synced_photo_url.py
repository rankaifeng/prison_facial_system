from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_add_armed_police_face'),
    ]

    operations = [
        migrations.AddField(
            model_name='prisonerarchive',
            name='last_synced_photo_url',
            field=models.CharField(blank=True, default='', help_text='用于增量同步，比对照片是否变化', max_length=512, verbose_name='上次同步到大华的照片URL'),
        ),
    ]
