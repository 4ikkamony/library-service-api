# Generated by Django 5.1.6 on 2025-03-01 12:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("borrowing_service", "0004_alter_borrowing_borrow_date"),
    ]

    operations = [
        migrations.AlterField(
            model_name="borrowing",
            name="borrow_date",
            field=models.DateField(auto_now_add=True),
        ),
    ]
