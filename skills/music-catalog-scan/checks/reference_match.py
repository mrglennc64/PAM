import csv
import os
from pathlib import Path

REFERENCE_ROOT = Path("/opt/ai-agency/music-catalog/reference")


def _load_society_index(society):
    society_dir = REFERENCE_ROOT / society.lower()
    if not society_dir.is_dir():
        return None
    index = {"isrc": set(), "iswc": set()}
    for csv_path in society_dir.glob("*.csv"):
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for ref_row in reader:
                isrc = (ref_row.get("isrc") or "").strip().upper()
                iswc = (ref_row.get("iswc") or "").strip().upper()
                if isrc:
                    index["isrc"].add(isrc)
                if iswc:
                    index["iswc"].add(iswc)
    return index


_INDEX_CACHE = {}


def _get_index(society):
    if society not in _INDEX_CACHE:
        _INDEX_CACHE[society] = _load_society_index(society)
    return _INDEX_CACHE[society]


def check(row):
    findings = []
    row_id = str(row.get("track_id", "")).strip()
    society = str(row.get("society", "")).strip().upper()

    if society not in {"STIM", "ICE", "MLC"}:
        return findings

    index = _get_index(society)
    if index is None:
        findings.append({
            "row_id": row_id,
            "severity": "info",
            "category": "reference_mismatch",
            "field": "society",
            "observed": society,
            "expected": f"local export at {REFERENCE_ROOT}/{society.lower()}/",
            "confidence": 0.99,
            "suggested_action": f"No local {society} reference export available — cannot verify",
            "requires_human_review": False,
        })
        return findings

    isrc = str(row.get("isrc", "")).strip().upper()
    iswc = str(row.get("iswc", "")).strip().upper()

    if isrc and isrc not in index["isrc"]:
        findings.append({
            "row_id": row_id,
            "severity": "warning",
            "category": "reference_mismatch",
            "field": "isrc",
            "observed": isrc,
            "expected": f"present in local {society} export",
            "confidence": 0.85,
            "suggested_action": f"ISRC not found in {society} reference — confirm registration or refresh export",
            "requires_human_review": True,
        })

    if iswc and iswc not in index["iswc"]:
        findings.append({
            "row_id": row_id,
            "severity": "warning",
            "category": "reference_mismatch",
            "field": "iswc",
            "observed": iswc,
            "expected": f"present in local {society} export",
            "confidence": 0.82,
            "suggested_action": f"ISWC not found in {society} reference — confirm registration or refresh export",
            "requires_human_review": True,
        })

    return findings


def check_batch_setup():
    _INDEX_CACHE.clear()
