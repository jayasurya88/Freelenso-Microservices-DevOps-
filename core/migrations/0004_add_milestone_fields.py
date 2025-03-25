from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_alter_chatroom_options_alter_chatmessage_sender_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectmilestone',
            name='completion_notes',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='projectmilestone',
            name='completed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='projectmilestone',
            name='feedback',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='projectfile',
            name='milestone',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deliverable_files', to='core.projectmilestone'),
        ),
    ] 