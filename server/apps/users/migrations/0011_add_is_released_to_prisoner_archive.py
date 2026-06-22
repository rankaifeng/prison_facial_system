from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_add_prisoner_archive'),
    ]

    operations = [
        migrations.AddField(
            model_name='prisonerarchive',
            name='is_released',
            field=models.BooleanField(default=False, verbose_name='是否已释放', db_index=True),
        ),
    ]
