# Generated by Django 4.2.2 on 2024-03-17 20:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0008_alter_chessgame_board_state_alter_chessgame_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='player',
            name='rating',
            field=models.IntegerField(default=-1),
        ),
    ]
