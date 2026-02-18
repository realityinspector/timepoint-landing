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

## What Flash Needs to Support

### 1. Auth0 JWT Verification (replacing/supplementing Apple Sign-In)

Flash currently validates Apple identity tokens directly. Auth0 wraps Apple Sign-In as a social connection AND adds web-friendly login (email, Google, GitHub).

Two integration paths:
- **Path A (recommended):** timepoint-billing validates Auth0 JWTs, resolves user identity, calls Flash with service key + `X-User-ID` header. Flash trusts the forwarded identity. Minimal Flash changes.
- **Path B:** Flash validates Auth0 JWTs directly alongside Apple tokens. More self-contained but duplicates Auth0 config across services.

Either way, Flash's User model needs to evolve from `apple_sub` to a more generic `auth_provider_sub` (or keep `apple_sub` and add `auth0_sub`).

### 2. Service-to-Service Credit Grants

timepoint-billing will call Flash to grant credits after Stripe/IAP payments:

```
POST /api/v1/credits/admin/grant
Headers: X-Admin-Key: {ADMIN_API_KEY}
Body: {
  "user_id": "uuid",
  "amount": 100,
  "description": "Stripe purchase: 100 credits ($9.99)"
}
```

This endpoint **already exists**. Billing just needs the `ADMIN_API_KEY`.

### 3. Service Key Calls from Clockchain

Clockchain workers generate scenes autonomously (unmetered, system-level):

```
POST /api/v1/timepoints/generate/sync
Headers: X-Service-Key: {FLASH_SERVICE_KEY}
Body: {"query": "Rome, 15 March 44 BCE", "preset": "balanced"}
```

Flash should handle service-key-only calls (no user context) as system generations:
- No credits deducted
- `visibility: PUBLIC`
- `user_id: null`

### 4. Calls from Billing (user-initiated, metered)

Billing relays user generation requests after verifying auth + checking credits:

```
POST /api/v1/timepoints/generate/stream
Headers: X-Service-Key: {FLASH_SERVICE_KEY}
         X-User-ID: {auth0_user_id}
Body: {"query": "...", "preset": "hd"}
```

Flash looks up or creates the user, deducts credits, generates.

### 5. CORS

If Flash is always called server-to-server (never directly from browser), disable CORS (`CORS_ENABLED=false`). All browser requests go through timepoint-billing (api.timepointai.com) or timepoint-app's backend.

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
                                                  │ service key
developer ─────────► timepoint-billing ───────────┘
(API key)                                         ▲
                                                  │ service key (unmetered)
                     timepoint-clockchain ────────┘
                     (autonomous workers)
```

Flash is the **execution engine**. Billing is the **front door**. Clockchain is the **autonomous operator**.

---

**TIMEPOINT · Synthetic Time Travel™**
