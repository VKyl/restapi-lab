from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kmartists', '0003_user_credentials'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='microsoft_id',
            field=models.CharField(max_length=255, null=True, unique=True),
        ),
    ]
