from django.urls import path

from . import views

urlpatterns = [
    path("upload/", views.upload_file, name="upload-file"),
    path("process/", views.process_file, name="process-file"),
    path("uploads/<int:upload_id>/", views.upload_detail, name="upload-detail"),
    path("uploads/<int:upload_id>/download/", views.download_processed, name="download-processed"),
]

