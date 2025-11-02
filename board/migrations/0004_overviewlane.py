from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("board", "0003_board_model"),
    ]

    operations = [
        migrations.CreateModel(
            name="OverviewLane",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("filters", models.JSONField(blank=True, default=dict)),
                ("position", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["position", "created_at", "id"],
            },
        ),
    ]
