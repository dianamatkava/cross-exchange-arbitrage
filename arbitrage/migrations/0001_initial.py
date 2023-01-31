# Generated by Django 4.1.5 on 2023-01-31 14:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TradingViewData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hash_pair', models.CharField(max_length=255, unique=True)),
                ('exchange', models.CharField(max_length=50)),
                ('name', models.CharField(max_length=50)),
                ('cur_1', models.CharField(max_length=16)),
                ('cur_2', models.CharField(max_length=16)),
                ('price_1', models.FloatField()),
                ('price_2', models.FloatField()),
                ('type', models.CharField(max_length=50)),
                ('subtype', models.CharField(max_length=50)),
                ('date', models.DateTimeField(auto_now=True)),
                ('reversed', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name_plural': 'Trading View Data',
            },
        ),
        migrations.CreateModel(
            name='CrossExchangeArbitrage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hash_pair', models.CharField(max_length=255, unique=True)),
                ('date', models.DateTimeField(auto_now=True)),
                ('hash_pair_1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hash_pair_1', to='arbitrage.tradingviewdata', to_field='hash_pair')),
                ('hash_pair_2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hash_pair_2', to='arbitrage.tradingviewdata', to_field='hash_pair')),
                ('hash_pair_3', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='hash_pair_3', to='arbitrage.tradingviewdata', to_field='hash_pair')),
                ('hash_pair_4', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='hash_pair_4', to='arbitrage.tradingviewdata', to_field='hash_pair')),
            ],
            options={
                'verbose_name_plural': 'Cross-Exchange Arbitrage',
            },
        ),
    ]
