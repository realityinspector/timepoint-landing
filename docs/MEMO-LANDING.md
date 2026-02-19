# MEMO: timepoint-landing
**From:** timepoint-landing · Feb 2026
**Re:** What the landing page gets wrong now that the platform is built

---

## 1. What This Repo Is

**timepoint-landing** is the static marketing page at `timepointai.com`. Single HTML file, no build step, nginx on Railway. It presents TIMEPOINT as a one-man AI lab focused on synthetic time travel — Flash, Daedalus, Proteus, SNAG Bench, and the Clockchain vision.

That positioning is correct. The alpha services behind it don't need to be the pitch.

This memo tracks what's **factually stale** on the page now that the platform has been built out.

---

## 2. What's Stale

### The Clockchain is live, but the page says "check back soon"

The clockchain-callout section says:

> "Check back soon for updates on the Clockchain project."

The Clockchain is deployed and running. It has:
- NetworkX graph with seed events + autonomous expansion
- Browse, search, today-in-history, random, graph neighbors, stats APIs
- LLM content judge (Gemini-based approve/reject)
- Daily "Today in History" auto-generation cron
- 60+ tests

The callout should reflect that it exists, not that it's coming. The 2022 blog post link is fine to keep.

### Flash stats are outdated

The page says:
- "14 specialized agents" → now **20+ agents**
- "630+ tests" → flash-deploy (the production fork) has **530+ tests** with billing + clockchain proxy; flash dev repo still has 630+

The product-stats line and pipeline diagram reference 14 agents. The pipeline ASCII art may need updating if the agent count/names have changed significantly.

### The "TRY FLASH" CTA uses a raw Railway URL

```
https://timepoint-flash-deploy-production.up.railway.app/docs
```

If `api.timepointai.com` is live and pointing at flash-deploy, the CTA should use the custom domain instead. This appears in 3 places:
- Hero CTA ("TRY FLASH — LIVE API")
- Flash product card ("TRY FLASH — LIVE API" button)
- Quickstart terminal blocks (curl example + base URL comment)

### README.md references the old Python backend

The README mentions:
- "Rollback" section with `git push origin archive/v2-api-backend:main --force`
- This references a FastAPI backend that was removed when the repo became static HTML

The README should just describe what the repo is now: static HTML + nginx + Railway.

### DESIGN.md says "served by FastAPI at `/`"

In Section 10 "Implementation Notes":
> `index.html` — Landing page (served by FastAPI at `/`)

It's served by nginx, not FastAPI.

---

## 3. What's NOT Stale (Leave Alone)

- **Lab positioning** — correct, this is a one-man lab, not a consumer product page
- **Flash / Daedalus / Proteus / SNAG Bench** — the four-product structure is right
- **The System flow** (Section 01) — still accurate as a conceptual description
- **SNAG Bench section** — correctly described as a scoring paradigm, leaderboard is "coming soon" which is true
- **Use cases** — all still valid
- **The Vision** (Clockchain, PORTALS) — the vision framing is fine even though Clockchain v1 is live
- **Open Source section** — repos are correctly linked
- **Design system** — CSS, typography, motifs all correct and shared with the web app memo
- **Scene gallery** — the three scene cards are fine
- **Daedalus examples** — still accurate

---

## 4. What Could Be Added (Optional, Not Required)

These are opportunities, not obligations:

- **Clockchain section or mention** — now that it's live, the landing page could show it as a real capability (browse temporal URLs, search history, graph visualization) rather than just a vision. But it can also stay as-is if the vision framing is preferred.
- **Canonical temporal URLs** — the `/{year}/{month}/{day}/{time}/{country}/{region}/{city}/{slug}` format is a distinctive feature that could be compelling on the landing page. Example: `/-44/march/15/1030/italy/lazio/rome/assassination-of-julius-caesar`
- **Live Clockchain data** — the landing page could pull from `/api/v1/clockchain/today` or `/stats` to show real graph stats instead of static text. But this adds a runtime dependency to a static page.

---

## 5. Concrete Fixes (Small)

| Fix | Where | Effort |
|-----|-------|--------|
| Update Clockchain callout — remove "check back soon", note it's live | `index.html` line ~600 | 1 min |
| Update agent count 14 → 20+ | `index.html` lines ~621, ~638 | 1 min |
| Replace Railway URL with `api.timepointai.com` (3 places) | `index.html` lines ~546, ~631, ~959-971 | 2 min |
| Update README to remove old rollback section | `README.md` | 1 min |
| Fix "served by FastAPI" → "served by nginx" in DESIGN.md | `DESIGN.md` line ~232 | 1 min |

---

## 6. Services Reference

| Service | Repo | Domain | Status |
|---------|------|--------|--------|
| **Landing** | **timepoint-landing** | `timepointai.com` | **THIS REPO — Live** |
| Flash-deploy | timepoint-flash-deploy | `api.timepointai.com` | Live (gateway) |
| Billing | timepoint-billing | *(internal)* | Live v0.4.0 |
| Clockchain | timepoint-clockchain | *(internal)* | Live |
| Web App | timepoint-web-app | `app.timepointai.com` | Planned |
| iPhone App | timepoint-iphone-app | *(App Store)* | Live |

---

**TIMEPOINT · Synthetic Time Travel**

*"The landing page is the front door. It sells the lab, not the infrastructure."*
