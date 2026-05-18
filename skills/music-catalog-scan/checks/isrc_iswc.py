import re

ISRC_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$")
ISWC_RE = re.compile(r"^T-?\d{3}\.?\d{3}\.?\d{3}-?\d$")


def check(row):
    findings = []
    row_id = str(row.get("track_id", "")).strip()

    isrc = str(row.get("isrc", "")).strip()
    if not isrc:
        findings.append({
            "row_id": row_id,
            "severity": "error",
            "category": "missing_isrc",
            "field": "isrc",
            "observed": "",
            "expected": "12-char ISRC (CCXXXYYNNNNN)",
            "confidence": 0.99,
            "suggested_action": "Request ISRC from label or assign new code via local registrar",
            "requires_human_review": True,
        })
    elif not ISRC_RE.match(isrc):
        findings.append({
            "row_id": row_id,
            "severity": "error",
            "category": "invalid_format",
            "field": "isrc",
            "observed": isrc,
            "expected": "12-char ISRC matching ^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$",
            "confidence": 0.98,
            "suggested_action": "Correct ISRC formatting",
            "requires_human_review": True,
        })

    iswc = str(row.get("iswc", "")).strip()
    if not iswc:
        findings.append({
            "row_id": row_id,
            "severity": "warning",
            "category": "missing_iswc",
            "field": "iswc",
            "observed": "",
            "expected": "ISWC matching T-DDD.DDD.DDD-D",
            "confidence": 0.95,
            "suggested_action": "Submit work to society for ISWC assignment",
            "requires_human_review": True,
        })
    elif not ISWC_RE.match(iswc):
        findings.append({
            "row_id": row_id,
            "severity": "error",
            "category": "invalid_format",
            "field": "iswc",
            "observed": iswc,
            "expected": "ISWC matching ^T-?\\d{3}\\.?\\d{3}\\.?\\d{3}-?\\d$",
            "confidence": 0.97,
            "suggested_action": "Correct ISWC formatting",
            "requires_human_review": True,
        })

    return findings
