# Generated by Django 3.1.7 on 2021-03-29 09:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_auto_20210328_1230'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='completed_courier_type',
            field=models.CharField(blank=True, max_length=4, null=True),
        ),
    ]
