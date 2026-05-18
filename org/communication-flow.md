# Communication flow

```
                       GLENN
                         ▲
                         │  status / questions / approvals
                         │
                       PAM (CEO)
                       /        \
                      /          \
                     ▼            ▼
                  ARIS          VESTA
                (VP Biz)      (VP Personal)
                  │ │ │ │ │       │
                  ▼ ▼ ▼ ▼ ▼       ▼
                  Business      Calendar
                  sub-roles    + Email
```

## Inbound (Glenn → Pam)
Glenn writes a request. Pam decides:
1. **Is this business or personal?** Route to Aris or Vesta accordingly.
2. **Which sub-role applies?** Activate that role's skill spec.
3. **Does it need Glenn's approval before completion?** See decision tables in [pam-ceo.md](pam-ceo.md) and the VP charters.

## Outbound (any agent → Glenn)
Always concise:
- One-sentence headline (what changed / what's needed)
- Bullet points (3–5 max)
- Explicit "Pam recommends: X" if a decision is asked of Glenn
- No status theatre, no padding

## Status updates
- **Daily** — Pam posts brief in `dashboard/00-overview.md` "Today" block
- **Weekly** — Pam runs full review (`dashboard/08-weekly-review.md`)
- **On-demand** — Glenn asks, Pam answers from dashboard state, not from memory
