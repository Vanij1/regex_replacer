from __future__ import annotations

import io
import json
import math
import re
from pathlib import Path
from typing import Iterable

import pandas as pd

from .llm import suggest_regex


def _is_text_like(series: pd.Series) -> bool:
    return series.dtype == "object" or series.dtype.name.startswith("string")


def _clean_preview_frame(df: pd.DataFrame, limit: int = 50) -> list[dict]:
    preview = df.head(limit).copy()
    preview = preview.replace({math.nan: None})
    preview = preview.where(pd.notnull(preview), None)
    return preview.to_dict(orient="records")


def read_uploaded_file(path: str):
    suffix = Path(path).suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    if suffix == ".csv":
        return pd.read_csv(path)
    raise ValueError("Unsupported file type. Please upload a CSV or Excel file.")


def write_processed_file(df: pd.DataFrame, source_name: str) -> tuple[bytes, str]:
    suffix = Path(source_name).suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        return buffer.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    data = df.to_csv(index=False).encode("utf-8")
    return data, "text/csv"


def detect_text_columns(df: pd.DataFrame) -> list[str]:
    candidates = []
    for column in df.columns:
        series = df[column]
        if _is_text_like(series):
            candidates.append(str(column))
    return candidates


def normalize_flags(flag_text: str) -> int:
    flags = 0
    normalized = (flag_text or "i").lower()
    if "i" in normalized:
        flags |= re.IGNORECASE
    if "m" in normalized:
        flags |= re.MULTILINE
    if "s" in normalized:
        flags |= re.DOTALL
    return flags


def apply_transformation(
    df: pd.DataFrame,
    pattern_description: str,
    replacement_value: str,
    target_columns: Iterable[str] | None = None,
    transform_mode: str = "replace",
):
    suggestion = suggest_regex(pattern_description)
    regex = re.compile(suggestion.regex, normalize_flags(suggestion.flags))

    if target_columns:
        columns = [column for column in target_columns if column in df.columns]
    else:
        columns = detect_text_columns(df)

    updated = df.copy()
    replaced_cells = 0
    matched_rows = 0

    for column in columns:
        series = updated[column]
        if not _is_text_like(series):
            series = series.astype("object")

        def transform_value(value):
            nonlocal replaced_cells, matched_rows
            if pd.isna(value):
                return value
            text = str(value)
            if not regex.search(text):
                return value
            matched_rows += 1
            if transform_mode == "mask":
                result = regex.sub(lambda m: "*" * max(3, len(m.group(0))), text)
            else:
                result = regex.sub(replacement_value, text)
            if result != text:
                replaced_cells += 1
            return result

        updated[column] = series.apply(transform_value)

    return {
        "regex": suggestion.regex,
        "flags": suggestion.flags,
        "explanation": suggestion.explanation,
        "confidence": suggestion.confidence,
        "columns": columns,
        "replaced_cells": replaced_cells,
        "matched_rows": matched_rows,
        "processed_df": updated,
        "preview_rows": _clean_preview_frame(updated),
    }

