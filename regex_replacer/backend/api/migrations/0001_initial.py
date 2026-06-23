# Generated manually for the regex replacer app.

from django.db import migrations, models



class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="UploadBatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("original_name", models.CharField(max_length=255)),
                ("source_file", models.FileField(upload_to="uploads/")),
                ("processed_file", models.FileField(blank=True, null=True, upload_to="processed/")),
                ("file_type", models.CharField(default="csv", max_length=20)),
                ("row_count", models.PositiveIntegerField(default=0)),
                ("column_names", models.JSONField(blank=True, default=list)),
                ("target_columns", models.JSONField(blank=True, default=list)),
                ("pattern_description", models.TextField(blank=True, default="")),
                ("regex_pattern", models.TextField(blank=True, default="")),
                ("replacement_value", models.TextField(blank=True, default="")),
                (
                    "transform_mode",
                    models.CharField(
                        choices=[("replace", "Replace matches"), ("mask", "Mask matches")],
                        default="replace",
                        max_length=20,
                    ),
                ),
                ("processing_metadata", models.JSONField(blank=True, default=dict)),
                ("preview_rows", models.JSONField(blank=True, default=list)),
                ("processed_rows", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
