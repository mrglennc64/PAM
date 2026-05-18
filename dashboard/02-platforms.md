# 02 — Platforms

**Owner:** Aris → Platform Engineer (code) + Marketing (copy) + Ops Lead (status)
**Last updated:** 2026-05-18

---

## Kataloghub
**URL:** kataloghub.se
**Pitch (neutral):** File-based metadata validation for Nordic publishers.
**Pitch (Carina-tone):** Validerar filbaserad metadata. Identifierar strukturella avvikelser. Genererar valideringsrapport och arbetsblad.

### Pipeline
- [ ] Validation engine — wired to `skills/music-catalog-scan/` (ISRC/ISWC, role-splits, duplicates, reference-match against STIM/ICE/MLC)
- [ ] Pricing model — _to define_
- [ ] Publisher onboarding flow
- [ ] Website text (Carina-tone) — draft pending
- [ ] File-based validation workflows — documented

### Live skill
[`PAM/skills/music-catalog-scan/`](../skills/music-catalog-scan/) — Python skill with checks:
- `checks/isrc_iswc.py`
- `checks/role_splits.py`
- `checks/duplicates.py`
- `checks/reference_match.py`

Reference data: [`PAM/samples/ai-agency-samples/reference/`](../samples/ai-agency-samples/reference/) (STIM, ICE, MLC export samples).

---

## HeyRoya
**URL:** heyroya.se
**Pitch (neutral):** Metadata correction workspace with CWR v2.1-ready output.
**Pitch (Carina-tone):** Korrigerar metadata baserat på förlagsbeslut. Förbereder CWR v2.1-paket.

### Pipeline
- [ ] Correction workflow — UI flow defined
- [ ] Worksheet logic — column rules, validation per cell
- [ ] CWR v2.1 packet generation — encoder + transmission file
- [ ] Carina-tone content — landing, FAQ, onboarding email
- [ ] Intake → correction → export — end-to-end test pass

### Tone enforcement
**Mandatory Carina-tone.** See [../tone/carina-tone.md](../tone/carina-tone.md).

---

## TrapRoyaltiesPro
**URL:** traproyaltiespro.com
**Pitch (neutral):** US-facing creator metadata review.
**Pitch (Carina-tone):** Granskar creator-metadata. Identifierar strukturella gap inför PRO- eller distributörsinlämning.

### Pipeline
- [ ] US workflow — defined
- [ ] LLC formation — see [04-financial-planning.md](04-financial-planning.md)
- [ ] Pricing (USD)
- [ ] Marketing tasks (US channels — different from Nordic)
- [ ] Creator-side metadata workflows

---

## Perfect Hold AB (parent)
**Pitch:** Parent company holding Kataloghub, HeyRoya, and TrapRoyaltiesPro.

### Pipeline
- [ ] Parent company structure — defined
- [ ] Multi-vertical automation plan
- [ ] AB formation steps — see [04-financial-planning.md](04-financial-planning.md)
- [ ] Funding readiness checklist
