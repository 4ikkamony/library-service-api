from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("borrowing_service", "0002_alter_borrowing_book_alter_borrowing_user"),
    ]

    operations = [
        migrations.AlterField(
            model_name="borrowing",
            name="actual_return_date",
            field=models.DateField(blank=True, null=True),
        ),
    ]
