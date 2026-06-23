from django.db import models


class UploadBatch(models.Model):
    class TransformMode(models.TextChoices):
        REPLACE = "replace", "Replace matches"
        MASK = "mask", "Mask matches"

    original_name = models.CharField(max_length=255)
    source_file = models.FileField(upload_to="uploads/")
    processed_file = models.FileField(upload_to="processed/", blank=True, null=True)
    file_type = models.CharField(max_length=20, default="csv")
    row_count = models.PositiveIntegerField(default=0)
    column_names = models.JSONField(default=list, blank=True)
    target_columns = models.JSONField(default=list, blank=True)
    pattern_description = models.TextField(blank=True, default="")
    regex_pattern = models.TextField(blank=True, default="")
    replacement_value = models.TextField(blank=True, default="")
    transform_mode = models.CharField(
        max_length=20, choices=TransformMode.choices, default=TransformMode.REPLACE
    )
    processing_metadata = models.JSONField(default=dict, blank=True)
    preview_rows = models.JSONField(default=list, blank=True)
    processed_rows = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.original_name} ({self.pk})"

