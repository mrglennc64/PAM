# Platform Engineer

**Reports to:** Aris.

## Charter
Builds and maintains code for Kataloghub, HeyRoya, TrapRoyaltiesPro. Owns the validation skill and the CWR v2.1 packet pipeline.

## Live skill
[`PAM/skills/music-catalog-scan/`](../../skills/music-catalog-scan/) — Python:
- `scan.py` — entrypoint
- `checks/isrc_iswc.py` — ISRC/ISWC code validation
- `checks/role_splits.py` — composer/writer/publisher splits
- `checks/duplicates.py` — duplicate detection
- `checks/reference_match.py` — match against STIM/ICE/MLC
- `schema/input.schema.json` / `schema/output.schema.json`
- Reference samples in [`PAM/samples/ai-agency-samples/reference/`](../../samples/ai-agency-samples/reference/)

## Platforms (external)
Each lives in its own GitHub repo (per `archive/old-ai-agency/` notes, structure already designed):
- `kataloghub` — backend/frontend/workers/config
- `heyroya` — backend/frontend/jobs/config (CWR export)
- `traproyaltiespro` — backend, US-facing
- `perfect-hold-ab` — infra/ops repo (dashboards, scripts)

## Operating rules
- Never push directly to `main` on any platform repo — PR + Pam review.
- Tests must run green before merge.
- Schema changes require a written migration note in the relevant docs/ folder.
- Secrets stay in [secrets/](../../secrets/) — never in repo, never in chat.

## When to escalate
- Any change to public API
- Any schema migration that breaks existing data
- Any dependency upgrade with breaking changes
