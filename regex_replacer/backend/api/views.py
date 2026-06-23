from __future__ import annotations

import json
import mimetypes
from pathlib import Path

import pandas as pd
from django.conf import settings
from django.core.files.base import ContentFile
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from .models import UploadBatch
from .services import apply_transformation, detect_text_columns, read_uploaded_file, write_processed_file


def _json_body(request):
    if request.body:
        return json.loads(request.body.decode("utf-8"))
    return {}


def _serialize_batch(batch: UploadBatch):
    return {
        "id": batch.id,
        "original_name": batch.original_name,
        "file_type": batch.file_type,
        "row_count": batch.row_count,
        "column_names": batch.column_names,
        "target_columns": batch.target_columns,
        "pattern_description": batch.pattern_description,
        "regex_pattern": batch.regex_pattern,
        "replacement_value": batch.replacement_value,
        "transform_mode": batch.transform_mode,
        "processing_metadata": batch.processing_metadata,
        "preview_rows": batch.preview_rows,
        "processed_rows": batch.processed_rows,
        "download_url": (
            f"/api/uploads/{batch.id}/download/" if batch.processed_file else None
        ),
        "source_url": batch.source_file.url if batch.source_file else None,
    }


@csrf_exempt
@require_http_methods(["POST"])
def upload_file(request):
    uploaded = request.FILES.get("file")
    if not uploaded:
        return JsonResponse({"error": "No file uploaded."}, status=400)

    suffix = Path(uploaded.name).suffix.lower()
    if suffix not in {".csv", ".xlsx", ".xls"}:
        return JsonResponse({"error": "Please upload a CSV or Excel file."}, status=400)

    batch = UploadBatch.objects.create(
        original_name=uploaded.name,
        source_file=uploaded,
        file_type=suffix.lstrip("."),
    )

    try:
        df = read_uploaded_file(batch.source_file.path)
    except Exception as exc:
        batch.delete()
        return JsonResponse({"error": str(exc)}, status=400)

    batch.row_count = int(df.shape[0])
    batch.column_names = list(df.columns.astype(str))
    batch.preview_rows = df.head(50).fillna("").to_dict(orient="records")
    batch.target_columns = detect_text_columns(df)
    batch.save()

    return JsonResponse({"upload": _serialize_batch(batch)})


@csrf_exempt
@require_http_methods(["POST"])
def process_file(request):
    data = _json_body(request)
    batch_id = data.get("upload_id")
    description = (data.get("pattern_description") or "").strip()
    replacement_value = data.get("replacement_value", "")
    target_columns = data.get("target_columns") or []
    transform_mode = data.get("transform_mode", "replace")

    if not batch_id:
        return JsonResponse({"error": "upload_id is required."}, status=400)
    if not description:
        return JsonResponse({"error": "pattern_description is required."}, status=400)

    batch = get_object_or_404(UploadBatch, pk=batch_id)

    try:
        df = read_uploaded_file(batch.source_file.path)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    result = apply_transformation(
        df=df,
        pattern_description=description,
        replacement_value=replacement_value,
        target_columns=target_columns,
        transform_mode=transform_mode,
    )

    processed_bytes, mime_type = write_processed_file(
        result["processed_df"], batch.original_name
    )
    output_name = Path(batch.original_name).stem + "_processed"
    output_suffix = ".xlsx" if mime_type.endswith("sheet") else ".csv"
    processed_filename = output_name + output_suffix
    batch.pattern_description = description
    batch.replacement_value = replacement_value
    batch.regex_pattern = result["regex"]
    batch.transform_mode = transform_mode
    batch.target_columns = result["columns"]
    batch.processing_metadata = {
        "flags": result["flags"],
        "explanation": result["explanation"],
        "confidence": result["confidence"],
        "replaced_cells": result["replaced_cells"],
        "matched_rows": result["matched_rows"],
    }
    batch.processed_rows = result["preview_rows"]
    batch.processed_file.save(
        processed_filename, ContentFile(processed_bytes), save=True
    )

    return JsonResponse(
        {
            "upload": _serialize_batch(batch),
            "message": "Processing complete.",
            "regex": result["regex"],
            "flags": result["flags"],
            "explanation": result["explanation"],
            "confidence": result["confidence"],
        }
    )


@require_GET
def upload_detail(request, upload_id: int):
    batch = get_object_or_404(UploadBatch, pk=upload_id)
    return JsonResponse({"upload": _serialize_batch(batch)})


@require_GET
def download_processed(request, upload_id: int):
    batch = get_object_or_404(UploadBatch, pk=upload_id)
    if not batch.processed_file:
        return JsonResponse({"error": "No processed file found."}, status=404)
    return FileResponse(batch.processed_file.open("rb"), as_attachment=True, filename=batch.processed_file.name.split("/")[-1])
