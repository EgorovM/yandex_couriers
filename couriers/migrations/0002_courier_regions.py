# Generated by Django 3.1.7 on 2021-03-22 14:12

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('couriers', '0001_initial'),
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='courier',
            name='regions',
            field=models.ManyToManyField(to='orders.Region'),
        ),
    ]
