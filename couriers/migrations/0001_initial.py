# Generated by Django 3.1.7 on 2021-03-22 14:12

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Courier',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('courier_type', models.CharField(choices=[('foot', 'пеший курьер'), ('bike', 'велокурьер'), ('car', 'курьер на автомобиле')], max_length=4)),
                ('working_hours', models.CharField(max_length=1024)),
                ('rating', models.DecimalField(decimal_places=2, max_digits=6)),
                ('earning', models.IntegerField()),
            ],
        ),
    ]
