# Generated by Django 3.2.9 on 2021-11-16 10:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0002_populate_initial_species'),
    ]

    operations = [
        migrations.AddField(
            model_name='occurrence',
            name='occurrence_id',
            field=models.TextField(default='1'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='occurrence',
            name='stable_id',
            field=models.CharField(default='1', max_length=40),
            preserve_default=False,
        ),
    ]
