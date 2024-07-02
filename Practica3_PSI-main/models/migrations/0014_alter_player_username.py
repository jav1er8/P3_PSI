# Generated by Django 4.2.2 on 2024-05-02 22:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0013_alter_chessgame_blackplayer_alter_chessgame_end_time_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='player',
            name='username',
            field=models.CharField(default='', help_text='The name of the Player', max_length=100, unique=True),
        ),
    ]
