from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_add_is_released_to_prisoner_archive'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exitentryrecord',
            name='exit_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='出监日期'),
        ),
        migrations.AlterField(
            model_name='exitentryrecord',
            name='entry_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='入监日期'),
        ),
    ]
