# Generated by Django 5.1.2 on 2024-12-11 08:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_dashbaord', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scrapperloader',
            name='isScrapperCompleted',
        ),
        migrations.RemoveField(
            model_name='scrapperloader',
            name='isScrapperFailed',
        ),
        migrations.RemoveField(
            model_name='scrapperloader',
            name='isScrapperPaused',
        ),
        migrations.RemoveField(
            model_name='scrapperloader',
            name='isScrapperResumed',
        ),
        migrations.RemoveField(
            model_name='scrapperloader',
            name='isScrapperRunning',
        ),
        migrations.RemoveField(
            model_name='scrapperloader',
            name='isScrapperStarted',
        ),
        migrations.RemoveField(
            model_name='scrapperloader',
            name='isScrapperStopped',
        ),
        migrations.AddField(
            model_name='scrapperloader',
            name='scrapper_status',
            field=models.CharField(default='idle', max_length=255),
        ),
        migrations.AddField(
            model_name='scrapperloader',
            name='scrapper_status_message',
            field=models.TextField(default=''),
        ),
    ]
