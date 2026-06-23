from django.contrib import admin

from .models import UploadBatch


@admin.register(UploadBatch)
class UploadBatchAdmin(admin.ModelAdmin):
    list_display = ("id", "original_name", "file_type", "row_count", "transform_mode", "created_at")
    search_fields = ("original_name", "pattern_description", "regex_pattern")
    list_filter = ("file_type", "transform_mode", "created_at")

