from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class RegexSuggestion:
    regex: str
    flags: str = "i"
    explanation: str = ""
    confidence: float = 0.6


def _catalog_fallback(description: str) -> RegexSuggestion:
    text = description.lower()
    catalog = [
        (r"email", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "email address"),
        (r"phone|mobile|telephone", r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{4}\b", "phone number"),
        (r"url|website|link", r"https?://[^\s]+", "web URL"),
        (r"ip address", r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "IP address"),
        (r"date", r"\b\d{4}-\d{2}-\d{2}\b", "ISO date"),
        (r"invoice", r"\bINV-\d+\b", "invoice code"),
        (r"postal|postcode|zip", r"\b\d{5}(?:-\d{4})?\b", "postal code"),
    ]
    for pattern, regex, label in catalog:
        if re.search(pattern, text):
            return RegexSuggestion(regex=regex, explanation=f"Matched common {label} wording.", confidence=0.8)
    return RegexSuggestion(regex=r".+", explanation="Fallback matched any non-empty text.", confidence=0.2)


def suggest_regex(description: str) -> RegexSuggestion:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _catalog_fallback(description)

    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    prompt = {
        "role": "system",
        "content": (
            "You convert natural-language pattern descriptions into JSON with keys "
            "`regex`, `flags`, `explanation`, and `confidence`. "
            "Return only JSON. Choose concise, practical regex for text column replacement."
        ),
    }
    user = {
        "role": "user",
        "content": f"Description: {description}",
    }
    body = json.dumps(
        {
            "model": model,
            "input": [prompt, user],
            "temperature": 0.1,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError):
        return _catalog_fallback(description)

    text_chunks = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"}:
                text_chunks.append(content.get("text", ""))
    raw = "".join(text_chunks).strip()
    if not raw:
        return _catalog_fallback(description)

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return _catalog_fallback(description)

    regex = parsed.get("regex") or r".+"
    flags = parsed.get("flags") or "i"
    explanation = parsed.get("explanation", "")
    confidence = float(parsed.get("confidence", 0.5))
    return RegexSuggestion(regex=regex, flags=flags, explanation=explanation, confidence=confidence)

