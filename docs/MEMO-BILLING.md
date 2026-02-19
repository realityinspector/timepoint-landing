# HANDOFF MEMO: timepoint-billing Agent
**From:** timepoint-landing · Feb 2026
**Re:** Billing microservice — Stripe, Apple IAP, subscriptions (internal, called by flash-deploy)

---

## 1. What You Are Building

**timepoint-billing** is an **internal payment processing microservice**. It handles Stripe, Apple IAP, and subscription management. It is NOT the public-facing API gateway — **flash-deploy** is the gateway at `api.timepointai.com`.

Billing is called by flash-deploy's billing proxy and by Stripe/Apple webhooks directly.

### What Billing Does
1. **Stripe payments** — checkout sessions, webhook handling, subscription lifecycle
2. **Apple IAP** — receipt verification, webhook handling
3. **Subscription management** — active/canceled/past_due tracking, periodic credit grants
4. **Product catalog** — credit packs and subscription tiers with pricing

### What Billing Does NOT Do
- ~~Auth0 identity~~ → flash-deploy handles JWT auth
- ~~API keys~~ → not yet built (future)
- ~~Usage metering~~ → not yet built (future)
- ~~Clockchain proxy~~ → flash-deploy handles this
- ~~Credit ledger~~ → Flash's DB owns the ledger; billing calls Flash to grant/spend

---

## 2. Full Service Map (As Built)

```
timepointai.com          → timepoint-landing     (static marketing)
app.timepointai.com      → timepoint-app         (frontend SPA)
api.timepointai.com      → timepoint-flash-deploy (THE GATEWAY)
(internal)               → timepoint-billing     ← THIS SERVICE
(internal)               → timepoint-clockchain  (graph index + workers)
```

### Data Flow

```
                    app.timepointai.com
                    (timepoint-app SPA)
                           │
                    JWT in every request
                           │
                           ▼
                    api.timepointai.com
                    ┌──────────────────┐
                    │ FLASH-DEPLOY     │  (the gateway)
                    │ (auth, credits,  │
                    │  generation)     │
                    │                  │
                    │ /api/v1/billing/ │──► BILLING (you)
                    │   proxy layer    │   /internal/billing/*
                    └──┬───────────────┘
                       │           ▲
              forward user         │ callback: grant/spend/check
              identity via         │ /internal/credits/*
              X-Service-Key +      │
              X-User-Id            │
                       │           │
                       ▼           │
                    FLASH-DEPLOY's credit ledger
```

```
Stripe webhooks    ──► POST /webhooks/stripe     (direct, signature-verified)
Apple webhooks     ──► POST /webhooks/apple      (direct, signature-verified)
```

---

## 3. Current Status (v0.3.0, 5 commits)

### What's Built

| Feature | Status |
|---------|--------|
| FastAPI microservice | Done |
| `flash_client.py` — calls Flash for user resolve, admin grant, balance, costs, generation | Done |
| `credits_client.py` — calls Flash's `/internal/credits/*` for grant/spend/check | Done |
| Stripe Checkout sessions | Done |
| Stripe webhook handler (checkout.session.completed, invoice.paid, payment_failed) | Done |
| Stripe subscription lifecycle (create, update, delete, period tracking) | Done |
| Stripe Customer Portal | Done |
| Apple IAP verification (JWS signed transaction) | Done |
| Apple App Store Server webhooks | Scaffolded |
| Product catalog (4 credit packs, 3 subscription tiers) | Done |
| SQLAlchemy models (ApplePurchase, StripeCustomer, BillingSubscription) | Done |
| Alembic migrations | Done |
| Service key auth (X-Service-Key) | Done |
| Health check | Done |

### What's NOT Built

| Feature | Status |
|---------|--------|
| Auth0 JWT validation | Not needed (flash-deploy handles auth) |
| API key management (developer keys) | Future |
| Usage metering | Future |
| Rate limiting | Future |
| CORS | Not needed (internal only, webhooks are direct) |

---

## 4. Architecture: Who Calls Whom

### Flash-deploy → Billing (via billing proxy)

Flash-deploy proxies these requests from the app to billing:

| Flash-deploy Route | Billing Route | Purpose |
|-------------------|---------------|---------|
| `GET /api/v1/billing/products` | `GET /internal/billing/products` | List credit packs + subscriptions |
| `GET /api/v1/billing/status` | `GET /internal/billing/status` | User's subscription status |
| `POST /api/v1/billing/stripe/checkout` | `POST /internal/billing/stripe/checkout` | Create Stripe Checkout session |
| `GET /api/v1/billing/stripe/portal` | `GET /internal/billing/stripe/portal` | Stripe Customer Portal URL |
| `POST /api/v1/billing/apple/verify` | `POST /internal/billing/apple/verify` | Verify Apple IAP |

Flash-deploy forwards user identity via headers:
```
X-Service-Key: {BILLING_API_KEY}
X-User-Id: {flash_user_uuid}
X-User-Email: {user_email}
```

### Billing → Flash-deploy (via flash_client.py)

After a successful payment, billing calls Flash to grant credits:

| Billing Calls | Flash Endpoint | Purpose |
|--------------|----------------|---------|
| `resolve_user()` | `POST /api/v1/users/resolve` | Find-or-create user by external_id |
| `admin_grant_credits()` | `POST /api/v1/credits/admin/grant` | Grant credits after payment |
| `get_balance()` | `GET /api/v1/credits/balance` | Query user balance |
| `get_costs()` | `GET /api/v1/credits/costs` | Get credit cost table |
| `relay_generate_sync()` | `POST /api/v1/timepoints/generate/sync` | Relay generation |
| `relay_generate_stream()` | `POST /api/v1/timepoints/generate/stream` | Relay SSE generation |

Uses headers:
```
X-Service-Key: {FLASH_SERVICE_KEY}      # service auth
X-Admin-Key: {FLASH_ADMIN_KEY}          # for admin grants
X-User-ID: {user_id}                    # for metered calls
```

### External → Billing (webhooks, direct)

```
Stripe  → POST /webhooks/stripe   (signature-verified, no proxy)
Apple   → POST /webhooks/apple    (signature-verified, no proxy)
```

---

## 5. Products & Pricing

### Credit Packs (one-time)

| Product ID | Name | Credits | Price |
|------------|------|---------|-------|
| `com.timepoint.flash.credits.10` | Starter | 10 | $2.99 |
| `com.timepoint.flash.credits.50` | Explorer | 50 | $9.99 |
| `com.timepoint.flash.credits.150` | Creator | 150 | $24.99 |
| `com.timepoint.flash.credits.500` | Studio | 500 | $69.99 |

### Subscriptions (monthly)

| Product ID | Name | Credits/Month | Price |
|------------|------|---------------|-------|
| `com.timepoint.flash.sub.explorer` | Explorer | 100 | $7.99/mo |
| `com.timepoint.flash.sub.creator` | Creator | 300 | $19.99/mo |
| `com.timepoint.flash.sub.studio` | Studio | 1,000 | $49.99/mo |

---

## 6. Stripe Integration (Built)

### Checkout Flow

1. User clicks "Buy Credits" in app
2. App calls `POST /api/v1/billing/stripe/checkout` → flash-deploy proxies to billing
3. Billing creates Stripe Checkout session with `metadata: {user_id, product_id}`
4. Returns `checkout_url` → app redirects user
5. User completes payment on Stripe
6. Stripe sends webhook to `POST /webhooks/stripe` (direct to billing)
7. Billing verifies signature, dispatches to handler:
   - **checkout.session.completed** → `flash_client.admin_grant_credits(transaction_type="stripe_purchase")`
   - **invoice.paid** → grant subscription renewal credits (`transaction_type="subscription_grant"`)
   - **invoice.payment_failed** → mark subscription `past_due`
   - **customer.subscription.updated/deleted** → update subscription status

### Subscription Lifecycle

- New subscription: creates `BillingSubscription` record, grants initial credits
- Renewal: `invoice.paid` webhook grants periodic credits
- Cancellation: marks subscription expired
- Past due: marks subscription past_due on payment failure

---

## 7. Apple IAP (Built)

### Verification Flow

1. iOS user purchases in-app
2. App sends signed transaction to `POST /api/v1/billing/apple/verify`
3. Flash-deploy proxies to billing `POST /internal/billing/apple/verify`
4. Billing verifies JWS signature
5. Idempotency check (by `originalTransactionId`)
6. Resolves product → credits
7. Calls `flash_client.admin_grant_credits(transaction_type="apple_iap")`
8. Records `ApplePurchase` in billing DB

---

## 8. Database Models

Billing has its own PostgreSQL database (NOT Flash's). `user_id` is a plain string (Flash UUID), no foreign key.

```python
class ApplePurchase(Base):
    user_id: str                    # Flash user UUID
    apple_original_transaction_id: str  # Unique, idempotency key
    product_id: str
    credits_granted: int
    price_milliunits: int | None
    currency: str | None
    status: PurchaseStatus          # completed, refunded

class StripeCustomer(Base):
    user_id: str                    # Unique per user
    stripe_customer_id: str         # Unique Stripe ID

class BillingSubscription(Base):
    user_id: str
    source: SubscriptionSource      # apple, stripe
    tier: str                       # explorer, creator, studio
    stripe_subscription_id: str | None
    apple_original_transaction_id: str | None
    status: SubscriptionStatus      # active, canceled, past_due, expired
    credits_per_period: int
    current_period_start: datetime | None
    current_period_end: datetime | None
    last_grant_at: datetime | None
```

---

## 9. Tech Stack

- **Framework:** FastAPI
- **Payments:** Stripe Python SDK, Apple App Store Server Library
- **Database:** PostgreSQL (own DB, via SQLAlchemy + asyncpg)
- **HTTP Client:** httpx (for Flash calls)
- **Migrations:** Alembic
- **Deployment:** Railway (Docker)
- **Python 3.11+**

### Env Vars

```bash
# Database
DATABASE_URL=postgresql+asyncpg://...

# Inter-service
MAIN_APP_INTERNAL_URL=http://timepoint-flash-deploy.railway.internal:8080
SERVICE_API_KEY=...          # Billing's own key (flash-deploy uses this to call billing)
FLASH_SERVICE_KEY=...        # Flash's service key (billing uses this to call flash)
FLASH_ADMIN_KEY=...          # Flash's admin key (for credit grants)

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Apple
APPLE_BUNDLE_ID=com.timepoint.flash
APPLE_APP_STORE_KEY_ID=...
APPLE_APP_STORE_ISSUER_ID=...
APPLE_APP_STORE_PRIVATE_KEY=...  # Base64-encoded
APPLE_APP_STORE_ENVIRONMENT=Production

# App URLs (Stripe redirects)
SUCCESS_URL=https://app.timepointai.com/billing/success
CANCEL_URL=https://app.timepointai.com/billing/cancel
```

---

## 10. Project Structure (As Built)

```
timepoint-billing/
├── src/
│   └── timepoint_billing/
│       ├── __init__.py
│       ├── main.py              # FastAPI app, lifespan, health check
│       ├── config.py            # BillingSettings (pydantic-settings)
│       ├── database.py          # AsyncSession, init/close DB
│       ├── models.py            # ApplePurchase, StripeCustomer, BillingSubscription
│       ├── products.py          # Credit packs + subscription tier definitions
│       ├── auth.py              # verify_service_key, get_user_from_headers
│       ├── routes.py            # /internal/billing/products, /status
│       ├── flash_client.py      # httpx client for Flash (resolve, grant, balance, generate)
│       ├── credits_client.py    # httpx client for Flash's /internal/credits/*
│       ├── stripe_/
│       │   ├── __init__.py
│       │   ├── routes.py        # /internal/billing/stripe/checkout, /portal
│       │   ├── checkout.py      # Stripe Checkout session creation
│       │   ├── webhooks.py      # POST /webhooks/stripe
│       │   └── subscriptions.py # Subscription lifecycle handler
│       └── apple/
│           ├── __init__.py
│           ├── routes.py        # /internal/billing/apple/verify
│           ├── verifier.py      # JWS transaction verification
│           └── webhooks.py      # POST /webhooks/apple
├── alembic/                     # Database migrations
├── tests/
├── pyproject.toml
├── Dockerfile
└── README.md
```

---

## 11. What Success Looks Like

### Done (v0.3.0)
- [x] FastAPI on Railway with health check
- [x] Service key auth for incoming requests
- [x] flash_client.py — resolve users, grant credits, relay generation
- [x] Stripe Checkout sessions
- [x] Stripe webhook handler
- [x] Stripe subscription lifecycle
- [x] Stripe Customer Portal
- [x] Apple IAP verification (idempotent)
- [x] Product catalog (4 packs, 3 subscriptions)
- [x] SQLAlchemy models + Alembic migrations

### Phase 2 (Future)
- [ ] API key management (developer keys: tp_live_*, tp_test_*)
- [ ] Usage metering per key
- [ ] Rate limiting per tier
- [ ] Developer portal / docs
- [ ] Billing admin panel
- [ ] Refund handling (Stripe refund webhooks → `flash_client.admin_grant_credits(transaction_type="refund", amount=-N)`)

---

## 12. Services Reference

| Service | Repo | Domain | Status |
|---------|------|--------|--------|
| Landing | timepoint-landing | `timepointai.com` | Live |
| Flash-deploy | timepoint-flash-deploy | `api.timepointai.com` | Live (the gateway) |
| Billing | timepoint-billing | *(internal)* | **Live v0.3.0** |
| Clockchain | timepoint-clockchain | *(internal)* | Live |
| App | timepoint-app | `app.timepointai.com` | Planned |

---

**TIMEPOINT · Synthetic Time Travel**

*"Billing handles the money. Flash-deploy opens the door. Billing just processes the payments and tells Flash to add the credits."*
