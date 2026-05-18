def _parse_splits(s):
    if not s:
        return []
    out = []
    for token in str(s).replace(";", ",").split(","):
        token = token.strip()
        if not token:
            continue
        try:
            out.append(float(token.rstrip("%")))
        except ValueError:
            return None
    return out


def check(row):
    findings = []
    row_id = str(row.get("track_id", "")).strip()

    for field in ("writer_splits", "publisher_splits"):
        raw = row.get(field, "")
        splits = _parse_splits(raw)

        if splits is None:
            findings.append({
                "row_id": row_id,
                "severity": "error",
                "category": "invalid_format",
                "field": field,
                "observed": str(raw),
                "expected": "comma-separated percentages summing to 100",
                "confidence": 0.95,
                "suggested_action": f"Reformat {field} as comma-separated numeric percentages",
                "requires_human_review": True,
            })
            continue

        if not splits:
            continue

        total = round(sum(splits), 2)
        if abs(total - 100.0) > 0.01:
            findings.append({
                "row_id": row_id,
                "severity": "error",
                "category": "split_sum_mismatch",
                "field": field,
                "observed": str(total),
                "expected": "100",
                "confidence": 0.99,
                "suggested_action": f"Reconcile {field} so they sum to 100 (off by {round(total - 100.0, 2)})",
                "requires_human_review": True,
            })

    writers = [w.strip() for w in str(row.get("writers", "")).split(",") if w.strip()]
    writer_splits = _parse_splits(row.get("writer_splits", "")) or []
    if writers and writer_splits and len(writers) != len(writer_splits):
        findings.append({
            "row_id": row_id,
            "severity": "error",
            "category": "role_conflict",
            "field": "writers",
            "observed": f"{len(writers)} writers, {len(writer_splits)} splits",
            "expected": "writer count == split count",
            "confidence": 0.97,
            "suggested_action": "Align writer list and writer_splits cardinality",
            "requires_human_review": True,
        })

    return findings
