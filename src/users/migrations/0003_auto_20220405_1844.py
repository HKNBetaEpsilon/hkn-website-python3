# Generated by Django 2.2.10 on 2022-04-05 18:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20160218_1435'),
    ]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='major',
            field=models.CharField(blank=True, choices=[('CS', 'Computer Science'), ('CE', 'Computer Engineering'), ('EE', 'Electrical Engineering'), ('DS', 'Data Science')], max_length=2, null=True),
        ),
    ]
