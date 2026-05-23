# MediReady — Product Overview

Healthcare compliance platform. File-based audits and compliance tools. No EHR integrations, no PHI retention, no infrastructure changes.

- **URL:** health.usesmpt.com
- **Audience:** Healthcare compliance teams, SaaS platform operators
- **Source:** Downloads/MediReady-Overview.pdf (v1.0)

## How it works

1. **Input** — uploaded documents (clinical notes, policies, claim files, communication records)
2. **Processing** — ephemeral, PHI-safe, session-isolated; no data retained after the session
3. **Output** — structured compliance assets (audit reports, standards mappings, risk assessments, policies, SOPs)

## Part 1 — Audit engine (6 channels)

Each channel returns scores, severity-rated findings, required actions, and a PDF export.

1. **Claims Reimbursement** — coding accuracy, billing completeness, reimbursement risk flags
2. **HIPAA & Security** — safeguard adherence, access control indicators, breach risk scoring
3. **Documentation Quality** — record completeness, legibility, regulatory documentation standards
4. **Patient Communication** — consent language, notice clarity, patient-facing regulatory requirements
5. **Clinical Content** — care plan integrity, clinical note structure, guideline alignment
6. **Synthetic Reviewer Behavior** — simulates auditor review patterns; surfaces findings before external review

## Part 2 — Compliance Suite (5 standalone tools)

1. **Audit Plan Generator** — structured audit plan from organizational inputs
2. **Standards Mapping** — maps content to regulatory/clinical standards frameworks
3. **Document Gap Analysis** — identifies missing/incomplete elements vs. compliance requirements
4. **HIPAA Risk Assessment** — structured HIPAA Security Rule risk assessment
5. **Policy / SOP Generator** — draft policies and SOPs aligned to input context

## Pricing

### Free tier — $0
- 3 full MediReady audits / month
- 1 document per Compliance Suite tool / month
- Unlimited standards mapping (short inputs)
- 7-day output history
- Demo monitoring dashboard access

### Per-document
| Tool | Price |
|---|---|
| Audit Plan Generator | $29 / document |
| Standards Mapping | $19 / mapping |
| Document Gap Analysis | $49 / document |
| HIPAA Risk Assessment | $149 / assessment |
| Policy / SOP Generator | $29 / document |

### Suite subscriptions (waitlist-only)
| Tier | Price | Audience |
|---|---|---|
| Clinic | $99 / mo | Single-location practices, small clinical teams |
| Network / SaaS | $499 / mo | Multi-site networks, SaaS platform operators (most common) |
| Enterprise | $999+ / mo | Large health systems, enterprise compliance programs |

Free tier and per-document available immediately. Suite subscriptions are waitlist-only.

## Security model — PHI-safe by design

- **No PHI stored** — uploaded files not retained
- **Ephemeral processing** — isolated sessions, no recoverable data state
- **Encrypted in transit** — no plaintext transfer
- **Local storage for outputs** — Compliance Suite docs stored in user's browser, no server-side copies
- **HIPAA-aligned workflows** — follows HIPAA Security Rule operational standards; no BAA required for file-based, ephemeral use

## Access model

- **Public marketing site** — health.usesmpt.com (info, features, pricing)
- **Gated tool access** — all audit/compliance tools require password or invite; no open self-registration
- **Free tier evaluation** — qualified evaluators can test core functionality
