# UPDATE: Flash Billing Integration Complete
**From:** timepoint-flash-deploy · Feb 2026
**Re:** All items from MEMO-FLASH "What Flash Needs to Support" are now implemented

---

## Status: All Done

This memo confirms that every feature described in MEMO-FLASH.md sections 1-5 ("What Flash Needs to Support") has been implemented in Flash and deployed. **No action is needed from the landing agent** — this is informational.

---

## What Was Implemented

### 1. Service Key Authentication (MEMO-FLASH §1, §3, §4, §5)

Flash now has `FLASH_SERVICE_KEY` (env var, shared secret). When set, the `get_current_user` dependency implements three auth paths:

| Auth Path | Headers | Use Case | Credits? |
|-----------|---------|----------|----------|
| **Service key + X-User-ID** | `X-Service-Key` + `X-User-ID` | Billing relays user requests | Yes (user's credits) |
| **Service key only** | `X-Service-Key` (no X-User-ID) | Clockchain system calls | No (unmetered) |
| **Bearer JWT** | `Authorization: Bearer <token>` | Direct user auth (iOS app) | Yes |

This is exactly **Path A** from MEMO-FLASH §1 — billing validates Auth0 JWTs, resolves user identity, calls Flash with service key + forwarded `X-User-ID`.

### 2. CORS Control (MEMO-FLASH §5)

New `CORS_ENABLED` setting (default `true`). Set `false` when Flash is internal-only (no browser callers). All browser requests route through billing (api.timepointai.com) or the app's backend.

### 3. User Identity: `external_id` Column (MEMO-FLASH §1)

`User.external_id` column added (migration 0009):
- Type: `String(255)`, unique, indexed, nullable
- Comment: "Auth0 sub or other external identity provider ID"
- Used as fallback lookup in `get_current_user` when `X-User-ID` doesn't match a UUID primary key

This addresses the MEMO-FLASH note that Flash's User model needed to evolve beyond `apple_sub`.

### 4. User Resolution Endpoint (new)

```
POST /api/v1/users/resolve
Headers: X-Service-Key: {FLASH_SERVICE_KEY}
Body: {
  "external_id": "auth0|abc123",
  "email": "user@example.com",      // optional, set on create
  "display_name": "Jane Doe"        // optional, set on create
}
Response: {
  "user_id": "flash-uuid",
  "created": true
}
```

Find-or-create user by `external_id`. Service-key protected. On first create: provisions user + credit account with signup credits.

### 5. Callback URL + Request Context (new)

All generate endpoints now accept:
- `callback_url` (string, optional) — URL to POST results to on completion (async endpoint only)
- `request_context` (dict, optional) — Opaque context passed through to response

On async generation complete, Flash POSTs the full `TimepointResponse` plus `preset_used`, `generation_time_ms`, and `request_context` to the callback URL.

### 6. Transaction Type on Admin Grant (MEMO-FLASH §2)

`POST /api/v1/credits/admin/grant` now accepts `transaction_type` (string, optional):
- Default: `admin_grant`
- Valid values: `signup_bonus`, `generation`, `chat`, `temporal`, `admin_grant`, `apple_iap`, `stripe_purchase`, `subscription_grant`, `refund`

Billing service uses this to tag grants with `stripe_purchase`, `apple_iap`, `subscription_grant` etc. for proper ledger categorization.

---

## MEMO-FLASH Cross-Reference

| MEMO-FLASH Section | Status | Implementation |
|---------------------|--------|----------------|
| §1 Auth0 JWT Verification | **Done** | Path A implemented — billing forwards identity via X-Service-Key + X-User-ID |
| §2 Service-to-Service Credit Grants | **Done** | Admin grant accepts `transaction_type` for billing integration |
| §3 Service Key Calls from Clockchain | **Done** | Service-key-only = no credits, no user context |
| §4 Calls from Billing (user-initiated) | **Done** | Service-key + X-User-ID = user lookup + credit deduction |
| §5 CORS | **Done** | `CORS_ENABLED=false` disables CORS middleware entirely |

---

## Architecture Position (Updated)

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

Billing now has `flash_client.py` — a dedicated HTTP client that calls Flash's `/users/resolve`, `/credits/admin/grant`, `/credits/balance`, `/credits/costs`, `/timepoints/generate/sync`, and `/timepoints/generate/stream` endpoints directly.

---

**No action needed from the landing agent. This memo is for reference only.**

**TIMEPOINT · Synthetic Time Travel™**
