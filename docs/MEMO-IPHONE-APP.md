# HANDOFF MEMO: timepoint-iphone-app Agent
**From:** timepoint-landing · Feb 2026
**Re:** What's changed in the platform since you last integrated with flash-deploy

---

## 1. Context

You already talk to **timepoint-flash-deploy** at `api.timepointai.com`. This memo covers **what's been built around you** — new capabilities available through flash-deploy, new sibling services, and the web app that's coming.

You don't need to change how you authenticate or generate scenes. Everything below is additive.

---

## 2. Full Service Map (Current)

```
timepointai.com          → timepoint-landing        (static marketing)
app.timepointai.com      → timepoint-web-app        (web SPA, not yet built)
api.timepointai.com      → timepoint-flash-deploy   (THE GATEWAY — you call this)
(internal)               → timepoint-billing        (Stripe, Apple IAP, subscriptions)
(internal)               → timepoint-clockchain     (graph index, browse/search, workers)
(App Store)              → timepoint-iphone-app     ← THIS IS YOU
```

### Architecture

```
timepoint-iphone-app (you)        timepoint-web-app (future)
         │                                │
    Apple Sign-In JWT                Auth0 JWT (planned)
         │                                │
         └────────────┬───────────────────┘
                      ▼
               api.timepointai.com
         ┌──────────────────────────────┐
         │  FLASH-DEPLOY (gateway)      │
         │                              │
         │  Auth, credits, generation   │
         │  /api/v1/billing/*  → billing│
         │  /api/v1/clockchain/* → cc   │
         └──────────────────────────────┘
```

---

## 3. What's New: Clockchain Proxy (Browse & Search)

Flash-deploy now proxies the **Clockchain** — TIMEPOINT's spatiotemporal graph index. This gives you access to an ever-growing catalog of historical moments, organized by canonical temporal URLs.

### New Endpoints (all via flash-deploy)

```
GET  /api/v1/clockchain/browse              → root year segments
GET  /api/v1/clockchain/browse/{path}       → hierarchical browsing
GET  /api/v1/clockchain/moments/{path}      → full moment data + edges
GET  /api/v1/clockchain/today               → events matching today's date
GET  /api/v1/clockchain/random              → random public moment
GET  /api/v1/clockchain/search?q={query}    → full-text search with scoring
GET  /api/v1/clockchain/graph/neighbors/{path} → connected nodes + edge metadata
GET  /api/v1/clockchain/stats               → total nodes/edges, layer/type counts
```

All are read-only GET requests. No special auth needed for public data — your existing `X-Service-Key` or Bearer JWT works.

### Canonical Temporal URLs

Moments are addressed by path:

```
/{year}/{month}/{day}/{time}/{country}/{region}/{city}/{slug}
```

| Segment | Format | Examples |
|---------|--------|----------|
| `year` | Integer, negative for BCE | `1969`, `-44`, `2001` |
| `month` | Spelled out, lowercase | `march`, `november` |
| `day` | Integer, no zero-padding | `15`, `1`, `28` |
| `time` | 24hr, no colon | `1030`, `0900`, `2300` |
| `country` | Modern borders, lowercase | `italy`, `united-states` |
| `region` | State/province/region | `lazio`, `new-mexico` |
| `city` | City/locality | `rome`, `los-alamos` |
| `slug` | Auto-generated, kebab-case | `assassination-of-julius-caesar` |

Partial paths return listings:
- `/api/v1/clockchain/browse/1969` → all months with events in 1969
- `/api/v1/clockchain/browse/1969/july` → all days in July 1969
- `/api/v1/clockchain/browse/1969/july/20` → all events on July 20, 1969

### Content Layers

| Layer | Content | Source |
|-------|---------|--------|
| 0 | URL path + event name | Clockchain graph (bulk LLM expansion) |
| 1 | Metadata — date, figures, tags, one-liner, sources | Clockchain graph |
| 2 | Full Flash scene — narrative, image, characters, dialog | Flash DB (on-demand) |

Millions of Layer 0 nodes exist (cheap to generate). Thousands have Layer 2 scenes. Layer 0-1 makes the graph browsable before scenes are rendered.

### What This Enables in the App

- **Browse history** by era, year, month, day — hierarchical temporal navigation
- **"Today in History"** — daily curated moments from the Clockchain
- **Search** — find moments by keyword across names, descriptions, figures, tags
- **Discover related events** — graph neighbors show connected moments (contemporaneous, same-location, thematic, causal)
- **Generate on demand** — if a moment has Layer 0-1 but no scene, the user can spend credits to render it

---

## 4. What's New: Billing v0.4.0

Billing is now at **v0.4.0** with production-grade payment handling.

### What Changed (v0.3.0 → v0.4.0)

| Feature | Status |
|---------|--------|
| **Webhook idempotency** — `WebhookEvent` table deduplicates Stripe + Apple webhooks | New |
| **`StripePurchase` model** — mirrors `ApplePurchase`, tracks Stripe one-time purchases | New |
| **Refund handling** — `charge.refunded` webhook deducts credits | New |
| **Dispute handling** — `dispute.created` deducts, `dispute.closed` (won) restores | New |
| **Apple subscription lifecycle** — `SUBSCRIBED`, `DID_FAIL_TO_RENEW`, `REVOKE` handlers | New |
| `DISPUTED` purchase status | New |

### Endpoints You Already Use (unchanged)

```
POST /api/v1/billing/apple/verify         → verify Apple IAP (your main payment path)
GET  /api/v1/billing/products             → list credit packs + subscriptions
GET  /api/v1/billing/status               → user's subscription status
```

### Apple IAP Flow (unchanged)

1. User purchases in-app
2. App sends signed transaction to `POST /api/v1/billing/apple/verify`
3. Flash-deploy proxies to billing → verifies JWS → grants credits → returns result
4. Idempotent by `originalTransactionId` — safe to retry

### Apple Webhook Handling (new in v0.4.0)

Apple now sends App Store Server Notifications V2 directly to billing's `/webhooks/apple`. Billing handles:

- **SUBSCRIBED** → creates `BillingSubscription`, grants initial monthly credits
- **DID_RENEW** → grants renewal credits
- **DID_FAIL_TO_RENEW** → marks subscription `PAST_DUE`
- **AUTO_RENEW_DISABLED/ENABLED** → updates renewal status
- **EXPIRED** / **GRACE_PERIOD_EXPIRED** → marks subscription `EXPIRED`
- **REVOKE** → marks subscription `EXPIRED`
- **REFUND** → marks purchase `REFUNDED`, deducts credits

You don't need to handle these — billing processes them server-side. But your app should reflect the user's current subscription status by checking `GET /api/v1/billing/status`.

---

## 5. Products & Pricing

### Credit Packs (one-time, available via Apple IAP)

| Product ID | Name | Credits | Price |
|------------|------|---------|-------|
| `com.timepoint.flash.credits.10` | Starter | 10 | $2.99 |
| `com.timepoint.flash.credits.50` | Explorer | 50 | $9.99 |
| `com.timepoint.flash.credits.150` | Creator | 150 | $24.99 |
| `com.timepoint.flash.credits.500` | Studio | 500 | $69.99 |

### Subscriptions (monthly, available via Apple IAP)

| Product ID | Name | Credits/Month | Price |
|------------|------|---------------|-------|
| `com.timepoint.flash.sub.explorer` | Explorer | 100 | $7.99/mo |
| `com.timepoint.flash.sub.creator` | Creator | 300 | $19.99/mo |
| `com.timepoint.flash.sub.studio` | Studio | 1,000 | $49.99/mo |

### Credit Costs

| Operation | Credits |
|-----------|---------|
| Generate (balanced) | 5 |
| Generate (hd) | 10 |
| Generate (hyper) | 5 |
| Generate (gemini3) | 5 |
| Character chat | 1 |
| Temporal jump | 2 |
| Signup bonus | 50 (free) |

---

## 6. Public vs Private Timepoints

### Public Timepoints
- Generated autonomously by Clockchain workers → stored in Flash as `PUBLIC`
- Free to browse in the app (Layer 0-1 without login, full scenes with login)
- The ever-growing library

### Private Timepoints
- User-requested via the app → flash-deploy verifies credits → Flash generates as `PRIVATE`
- Only visible to the requesting user
- User can **publish** → becomes public, Clockchain indexes it
- Publishing enriches the library for everyone

### Relevant Endpoints

```
PATCH /api/v1/timepoints/{id}/visibility   → publish (private → public)
GET   /api/v1/users/me/timepoints          → user's scenes (private + published)
```

---

## 7. Existing Endpoints (Quick Reference)

These are unchanged — you already use most of them:

**Generation:**
```
POST /api/v1/timepoints/generate/stream   → SSE streaming generation
POST /api/v1/timepoints/generate/sync     → synchronous generation
POST /api/v1/timepoints/generate          → async generation (callback_url)
GET  /api/v1/timepoints/{id}              → fetch full scene
```

**Credits:**
```
GET  /api/v1/credits/balance              → credit balance
GET  /api/v1/credits/costs                → credit pricing per operation
GET  /api/v1/credits/history              → transaction ledger
```

**Auth:**
```
POST /api/v1/auth/login                   → session start (Apple Sign-In JWT)
GET  /api/v1/auth/me                      → user profile
```

**Interactions:**
```
POST /api/v1/interactions/chat            → character chat (1 credit)
POST /api/v1/temporal/jump                → temporal navigation (2 credits)
```

---

## 8. Generation Presets

4 quality presets available for scene generation:

| Preset | Model | Credits | Approx Time |
|--------|-------|---------|-------------|
| `balanced` | Gemini 2.5 Flash | 5 | ~90-110s |
| `hd` | Gemini 2.5 Flash + Nano Banana Pro (2K) | 10 | ~2.5 min |
| `hyper` | Gemini 2.0 Flash via OpenRouter | 5 | ~55s |
| `gemini3` | Gemini 3 Flash Preview | 5 | ~60s |

Default is `balanced` if no preset specified.

---

## 9. The Web App (Sibling, Not Competitor)

**timepoint-web-app** will live at `app.timepointai.com`. It's a separate repo, separate deploy, separate auth flow (Auth0 instead of Apple Sign-In). It shares the same backend (flash-deploy) and the same user accounts (via `external_id` + `/users/resolve`).

A user who signs in with Apple on the iPhone and with the same Apple account via Auth0 on the web will have the **same credit balance and timepoints** — Flash resolves identity through `external_id`.

The web app handles:
- Desktop browsing experience (hierarchical temporal navigation)
- Stripe Checkout for web payments (instead of Apple IAP)
- Auth0 for multi-provider login (Google, GitHub, email, Apple)
- Subscription management via Stripe Customer Portal

The iPhone app handles:
- Native iOS experience
- Apple Sign-In
- Apple IAP for payments
- StoreKit for subscription management

---

## 10. Services Reference

| Service | Repo | Domain | Status |
|---------|------|--------|--------|
| Landing | timepoint-landing | `timepointai.com` | Live |
| Flash-deploy | timepoint-flash-deploy | `api.timepointai.com` | Live (gateway: auth, credits, generation, billing + clockchain proxy) |
| Billing | timepoint-billing | *(internal)* | Live v0.4.0 (Stripe, Apple IAP, subscriptions, refunds, disputes) |
| Clockchain | timepoint-clockchain | *(internal)* | Live (graph, browse/search, workers) |
| Web App | timepoint-web-app | `app.timepointai.com` | Planned |
| iPhone App | timepoint-iphone-app | *(App Store)* | **THIS IS YOU** |

---

**TIMEPOINT · Synthetic Time Travel**

*"You already render moments. Now you can browse all of them — the Clockchain is open."*
