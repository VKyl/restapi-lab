import django.db.models.deletion
from django.db import migrations, models


def set_first_contributor_as_author(apps, schema_editor):
    Article = apps.get_model("kmartists", "Article")
    for article in Article.objects.filter(author=None):
        link = Article.contributors.through.objects.filter(article=article).order_by("id").first()
        if link:
            article.author_id = link.user_id
            article.save(update_fields=["author"])


class Migration(migrations.Migration):
    dependencies = [
        ("kmartists", "0004_user_microsoft_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="article",
            name="author",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="authored_articles",
                to="kmartists.user",
            ),
        ),
        migrations.RunPython(set_first_contributor_as_author, migrations.RunPython.noop),
    ]
