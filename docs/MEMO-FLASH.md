# MEMO: timepoint-flash Agent
**From:** timepoint-landing · Feb 2026
**Re:** Flash integration points for Clockchain + Billing + App

---

## Context

TIMEPOINT is a 5-service platform. Flash is the **central API server** — it owns scene generation, the credit ledger, character interactions, temporal navigation, and visibility control. It is the most mature service (630+ tests).

Flash was **designed with billing hooks already in place**:
- `BILLING_ENABLED` flag in config (`"Set automatically when timepoint-billing is installed"`)
- `TransactionType` enum includes `STRIPE_PURCHASE`, `APPLE_IAP`, `SUBSCRIPTION_GRANT`, `REFUND`
- `grant_credits()` and `spend_credits()` are ready for external callers
- `X-Service-Key` middleware for service-to-service auth
- `X-Admin-Key` for privileged operations (credit grants)

**Flash already lives at** `https://timepoint-flash-deploy-production.up.railway.app`.
**It will also be reachable as** `api.timepointai.com` (via timepoint-billing gateway).

---

## Full Service Map

```
timepointai.com          → timepoint-landing     (static marketing)
app.timepointai.com      → timepoint-app         (frontend SPA, browse + render)
api.timepointai.com      → timepoint-billing     (Auth0, Stripe, API keys, metered relay)
(internal)               → timepoint-flash       (credit ledger, generation, interactions)
(internal)               → timepoint-clockchain  (graph index, autonomous workers)
```

---

## What Flash Has Implemented (all complete)

All integration points are **live and deployed**. No further Flash changes needed.

### 1. Three Auth Paths

| Auth Path | Headers | Use Case | Credits? |
|-----------|---------|----------|----------|
| **Service key + X-User-ID** | `X-Service-Key` + `X-User-ID` | Billing relays user requests | Yes (user's credits) |
| **Service key only** | `X-Service-Key` (no X-User-ID) | Clockchain system calls | No (unmetered) |
| **Bearer JWT** | `Authorization: Bearer <token>` | Direct user auth (iOS app) | Yes |

This is **Path A** — billing validates Auth0 JWTs, resolves user identity, calls Flash with service key + forwarded `X-User-ID`.

### 2. User Identity: `external_id` Column

`User.external_id` added (migration 0009): `String(255)`, unique, indexed, nullable. Holds Auth0 `sub` or any external provider ID. Used as fallback lookup when `X-User-ID` doesn't match a UUID primary key. Flash no longer limited to `apple_sub`.

### 3. User Resolution Endpoint

```
POST /api/v1/users/resolve
Headers: X-Service-Key: {FLASH_SERVICE_KEY}
Body: {
  "external_id": "auth0|abc123",
  "email": "user@example.com",      // optional
  "display_name": "Jane Doe"        // optional
}
Response: { "user_id": "flash-uuid", "created": true }
```

Find-or-create by `external_id`. On first create: provisions user + credit account with signup credits.

### 4. Service-to-Service Credit Grants (with transaction_type)

```
POST /api/v1/credits/admin/grant
Headers: X-Admin-Key: {ADMIN_API_KEY}
Body: {
  "user_id": "uuid",
  "amount": 100,
  "transaction_type": "stripe_purchase",
  "description": "Stripe purchase: 100 credits ($9.99)"
}
```

`transaction_type` parameter accepts: `signup_bonus`, `generation`, `chat`, `temporal`, `admin_grant`, `apple_iap`, `stripe_purchase`, `subscription_grant`, `refund`.

### 5. Callback URL + Request Context

All generate endpoints accept:
- `callback_url` (string, optional) — Flash POSTs full result on completion
- `request_context` (dict, optional) — opaque context passed through to response

### 6. CORS Control

`CORS_ENABLED=false` disables CORS entirely. Flash is internal-only — all browser requests go through billing.

---

## What Flash Already Has (No Changes Needed)

- Credit ledger: `spend_credits()`, `grant_credits()`, `check_balance()` ✅
- Credit cost table per operation ✅
- Public/private visibility on Timepoint model ✅
- Service key middleware (`FLASH_SERVICE_KEY`) ✅
- Admin key for privileged ops (`ADMIN_API_KEY`) ✅
- Streaming SSE generation ✅
- Slug generation ✅
- 4 quality presets (hd/balanced/hyper/gemini3) ✅
- Character interactions (chat, dialog, surveys) ✅
- Temporal navigation (jump forward/backward) ✅
- User data export (GDPR SAR) ✅
- 630+ tests ✅

---

## Architecture Position

```
app.timepointai.com ──► timepoint-billing ──► FLASH (auth, credits, generate)
(frontend SPA)          (api.timepointai.com)     ▲
                        (Auth0, Stripe, keys)     │
                        Uses flash_client.py      │ X-Service-Key + X-User-ID
                        to call Flash directly    │
                                                  │
developer ─────────► timepoint-billing ───────────┘
(API key)                                         ▲
                                                  │ X-Service-Key (unmetered)
                     timepoint-clockchain ────────┘
                     (autonomous workers)
```

Flash is the **execution engine**. Billing is the **front door** (and already has `flash_client.py` built). Clockchain is the **autonomous operator**.

---

**TIMEPOINT · Synthetic Time Travel™**
