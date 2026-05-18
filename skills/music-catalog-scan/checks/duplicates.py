import re
from collections import defaultdict


def _normalize(s):
    s = str(s or "").lower().strip()
    s = re.sub(r"\([^)]*\)", "", s)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^\w\s]", "", s)
    return s.strip()


def check_batch(rows):
    findings = []
    by_key = defaultdict(list)
    by_isrc = defaultdict(list)

    for row in rows:
        title = _normalize(row.get("title"))
        artist = _normalize(row.get("artist"))
        if title and artist:
            by_key[(title, artist)].append(row)

        isrc = str(row.get("isrc", "")).strip().upper()
        if isrc:
            by_isrc[isrc].append(row)

    for (title, artist), group in by_key.items():
        if len(group) > 1:
            ids = [str(r.get("track_id", "")).strip() for r in group]
            for r in group:
                findings.append({
                    "row_id": str(r.get("track_id", "")).strip(),
                    "severity": "warning",
                    "category": "duplicate",
                    "field": "title+artist",
                    "observed": f"{title} / {artist}",
                    "expected": "unique (title, artist) per recording",
                    "confidence": 0.88,
                    "suggested_action": f"Review duplicate group: {ids}. Merge or differentiate (version, mix, recording_year).",
                    "requires_human_review": True,
                })

    for isrc, group in by_isrc.items():
        if len(group) > 1:
            ids = [str(r.get("track_id", "")).strip() for r in group]
            for r in group:
                findings.append({
                    "row_id": str(r.get("track_id", "")).strip(),
                    "severity": "error",
                    "category": "duplicate",
                    "field": "isrc",
                    "observed": isrc,
                    "expected": "unique ISRC per recording",
                    "confidence": 0.99,
                    "suggested_action": f"ISRC reused across rows: {ids}. ISRCs must be unique per recording — investigate.",
                    "requires_human_review": True,
                })

    return findings
