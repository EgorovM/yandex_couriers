# Generated by Django 3.1.7 on 2021-03-22 14:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('couriers', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weight', models.DecimalField(decimal_places=2, max_digits=6)),
                ('delivery_hours', models.CharField(max_length=1024)),
                ('region', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='orders.region')),
            ],
        ),
        migrations.CreateModel(
            name='CompletedOrder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assign_time', models.DateTimeField()),
                ('complete_time', models.DateTimeField(blank=True, null=True)),
                ('completed_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='couriers.courier')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='orders.order')),
            ],
        ),
    ]
