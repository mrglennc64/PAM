# 02 — Platforms

**Owner:** Aris → Platform Engineer (code) + Marketing (copy) + Ops Lead (status)
**Last updated:** 2026-05-24

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

## Bounty Hunter
**Code:** [`PAM/hunter/`](../hunter/) (cloned from github.com/mrglennc64/hunter on 2026-05-24)
**Pitch (neutral):** Internal pipeline that surfaces unclaimed SoundExchange royalties from Billboard / YouTube chart tracks, then finds the rights-holder contact for outreach.
**Status:** Code present locally, dependencies + API keys not yet installed.

### Pipeline (Python)
1. **Collect** — Billboard year-end + weekly + YouTube trending + remix / tier-2 / Atlanta collectors
2. **Resolve** — ISRC via MusicBrainz, Deezer fallback, optional Spotify re-resolve
3. **Enrich** — Chartmetric popularity filter (>60 = real cash)
4. **Score** — Sniper score: indie label / remix / recent / tier-2 artist
5. **Probe** — Stealth SoundExchange scrape (Playwright + residential proxies)
6. **Outreach** — Hunter.io finds buyer email per UNCLAIMED / CONFLICT lead

### What's left before first run
- [ ] `pip install -r hunter/requirements.txt` (includes Playwright — also needs `playwright install chromium`)
- [ ] Add `CHARTMETRIC_REFRESH_TOKEN`, `HUNTER_API_KEY`, `PROXIES` to `secrets/.env` (free-tier OK to start; see `hunter/.env.example`)
- [ ] Decide where probe output (`hunter/data/leads.csv`) gets reviewed — Pam dashboard vs. separate sheet
- [ ] First test run: `python hunter/run_pipeline.py --batch 50`

### Web pieces (not yet wired)
- `gap-finder-page.tsx`, `lead-intelligence-page.tsx` — React/TS dashboard components
- `gap-finder-probe-route.ts`, `isrc-lookup-route.ts` — API route handlers (Next.js style)
- These are loose files — no `package.json` in the repo, so they need a host (likely embedded into one of the existing platforms, or stood up as a separate Next app under `hunter/web/`)

### Spec
`hunter/_Bounty Hunter.pdf` is the original brief. Read this before changing pipeline logic.

---

## Perfect Hold AB (parent)
**Pitch:** Parent company holding Kataloghub, HeyRoya, and TrapRoyaltiesPro.

### Pipeline
- [ ] Parent company structure — defined
- [ ] Multi-vertical automation plan
- [ ] AB formation steps — see [04-financial-planning.md](04-financial-planning.md)
- [ ] Funding readiness checklist
