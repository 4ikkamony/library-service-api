# Generated by Django 5.1.6 on 2025-03-03 14:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("book_service", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="book",
            options={"ordering": ["title"]},
        ),
    ]
