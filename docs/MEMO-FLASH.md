# MEMO: timepoint-flash / timepoint-flash-deploy
**From:** timepoint-landing · Feb 2026
**Re:** Flash is the API gateway — auth, credits, generation, billing proxy, clockchain proxy

---

## Context

TIMEPOINT is a 5-service platform. **timepoint-flash-deploy** is the **unified API gateway** at `api.timepointai.com`. It handles auth, credits, scene generation, and proxies to billing and clockchain.

**Two repos, one deployed service:**
- **timepoint-flash** — the development repo (630+ tests, all core features)
- **timepoint-flash-deploy** — production fork with added billing proxy layer + internal credits API

Flash-deploy IS the front door. Billing and clockchain are internal services.

---

## Full Service Map (As Built)

```
timepointai.com          → timepoint-landing     (static marketing)
app.timepointai.com      → timepoint-app         (frontend SPA, browse + render)
api.timepointai.com      → timepoint-flash-deploy (THE GATEWAY)
(internal)               → timepoint-billing     (Stripe, Apple IAP, subscriptions)
(internal)               → timepoint-clockchain  (graph index, autonomous workers)
```

### Architecture

```
app.timepointai.com / iOS app
              │
       JWT (Apple Sign-In / Auth0 planned)
              │
              ▼
api.timepointai.com  (timepoint-flash-deploy)
┌─────────────────────────────────────────────────┐
│ FLASH-DEPLOY (unified gateway)                  │
│                                                 │
│ Core Flash:                                     │
│   Auth (JWT + service keys)                     │
│   Credits (ledger, balance, costs, admin grant) │
│   Generation (20+ AI agents, SSE streaming)     │
│   Characters (chat, dialog, surveys)            │
│   Temporal navigation                           │
│   User resolution (external_id for Auth0)       │
│                                                 │
│ Added in flash-deploy (not in flash):           │
│   /api/v1/billing/*  ──► billing (internal)     │
│   /internal/credits/* ◄── billing calls back    │
│   /api/v1/clockchain/* ──► clockchain (NEEDED)  │
└───────┬─────────────────────────┬───────────────┘
        │                         │
   BILLING_API_KEY         FLASH_SERVICE_KEY
        │                         │
        ▼                         ▼
 timepoint-billing         timepoint-clockchain
 (Stripe, Apple IAP)       (graph, browse, search)
```

---

## Flash-Deploy: What's Been Added Beyond Flash

### 1. Billing Proxy (`app/api/v1/billing_proxy.py`)

Proxies payment requests to the billing microservice:

| App Endpoint | Proxied To | Auth |
|-------------|-----------|------|
| `GET /api/v1/billing/products` | billing `/internal/billing/products` | None |
| `GET /api/v1/billing/status` | billing `/internal/billing/status` | JWT |
| `POST /api/v1/billing/stripe/checkout` | billing `/internal/billing/stripe/checkout` | JWT |
| `GET /api/v1/billing/stripe/portal` | billing `/internal/billing/stripe/portal` | JWT |
| `POST /api/v1/billing/apple/verify` | billing `/internal/billing/apple/verify` | JWT |

Requires: `BILLING_ENABLED=true`, `BILLING_API_KEY`, `BILLING_SERVICE_URL`

### 2. Internal Credits API (`app/api/v1/internal_credits.py`)

Called BY billing after payment to grant/spend credits in Flash's ledger:

| Endpoint | Called By | Purpose |
|----------|----------|---------|
| `POST /internal/credits/grant` | Billing | Grant credits after Stripe/Apple payment |
| `POST /internal/credits/spend` | Billing | Spend credits (for refunds) |
| `GET /internal/credits/check` | Billing | Check if user has sufficient credits |

Protected by `BILLING_API_KEY` (X-Service-Key header).

### 3. Config Additions

```python
# In flash-deploy's config.py (beyond flash):
BILLING_ENABLED: bool = False
BILLING_API_KEY: str = ""          # Shared secret with billing service
BILLING_SERVICE_URL: str = ""      # Billing's internal Railway URL
```

---

## What Flash Has (Core — Same in Both Repos)

### Three Auth Paths

| Auth Path | Headers | Use Case | Credits? |
|-----------|---------|----------|----------|
| **Service key + X-User-ID** | `X-Service-Key` + `X-User-ID` | Billing/clockchain relays user requests | Yes (user's credits) |
| **Service key only** | `X-Service-Key` (no X-User-ID) | Clockchain system calls | No (unmetered) |
| **Bearer JWT** | `Authorization: Bearer <token>` | Direct user auth (iOS app, web) | Yes |

### User Identity: `external_id` Column

`User.external_id` added (migration 0009): `String(255)`, unique, indexed, nullable. Holds Auth0 `sub` or any external provider ID. Used as fallback lookup when `X-User-ID` doesn't match a UUID primary key.

### User Resolution Endpoint

```
POST /api/v1/users/resolve
Headers: X-Service-Key: {FLASH_SERVICE_KEY}
Body: {
  "external_id": "auth0|abc123",
  "email": "user@example.com",
  "display_name": "Jane Doe"
}
Response: { "user_id": "flash-uuid", "created": true }
```

Find-or-create by `external_id`. On first create: provisions user + credit account with signup credits.

### Credit Ledger

- `spend_credits()`, `grant_credits()`, `check_balance()` — all atomic
- Immutable transaction log (CreditTransaction model)
- TransactionType enum: `signup_bonus`, `generation`, `chat`, `temporal`, `admin_grant`, `apple_iap`, `stripe_purchase`, `subscription_grant`, `refund`
- Credit costs: balanced=5, hd=10, hyper=5, gemini3=5, chat=1, temporal_jump=2
- Admin grant: `POST /api/v1/credits/admin/grant` with `X-Admin-Key` and `transaction_type`

### Generation

- 4 quality presets (hd/balanced/hyper/gemini3)
- Sync, async (with callback_url + request_context), and SSE streaming
- 20+ AI agents in pipeline (grounding, scene, characters, dialog, image, etc.)

### Other Features

- Public/private visibility on Timepoint model
- Streaming SSE generation
- Slug generation
- Character interactions (chat, dialog, surveys)
- Temporal navigation (jump forward/backward)
- User data export (GDPR SAR)
- CORS control (`CORS_ENABLED=false` for internal-only mode)
- 630+ tests

---

## Gap: Clockchain Proxy

Flash-deploy has `billing_proxy.py` but **no clockchain proxy**. The clockchain has a full API (browse, search, today, random, neighbors, stats) but it's not accessible from the public API.

**Needed:** A `clockchain_proxy.py` in flash-deploy (similar to billing_proxy.py) that forwards:
```
/api/v1/clockchain/*  →  CLOCKCHAIN_SERVICE_URL/api/v1/*
```

Config additions needed:
```python
CLOCKCHAIN_ENABLED: bool = False
CLOCKCHAIN_SERVICE_URL: str = ""
CLOCKCHAIN_SERVICE_KEY: str = ""
```

---

**TIMEPOINT · Synthetic Time Travel**
