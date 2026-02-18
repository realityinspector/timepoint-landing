# HANDOFF MEMO: timepoint-billing Agent
**From:** timepoint-landing · Feb 2026
**Re:** Build the billing gateway — Auth0, Stripe, API keys, metered relay at api.timepointai.com

---

## 1. What You Are Building

**timepoint-billing** is the **front door** to TIMEPOINT's platform. It lives at `api.timepointai.com` and handles everything Flash and Clockchain don't:

1. **Auth0 identity** — web login (email, Google, GitHub) + Apple Sign-In as social connection
2. **Stripe payments** — credit purchases, subscriptions
3. **Developer API keys** — per-developer keys with rate limits and usage tracking
4. **Metered relay** — proxies generation requests to Flash, deducting credits
5. **Graph data relay** — proxies browse/search requests to Clockchain

Billing is a **thin gateway**. It does NOT store scenes, maintain graphs, or run generation pipelines. It authenticates, meters, bills, and forwards.

---

## 2. Full Service Map

```
timepointai.com          → timepoint-landing     (static marketing)
app.timepointai.com      → timepoint-app         (frontend SPA)
api.timepointai.com      → timepoint-billing     ← YOU ARE BUILDING THIS
(internal)               → timepoint-flash       (credit ledger + generation)
(internal)               → timepoint-clockchain  (graph index + workers)
```

### Data Flow

```
                    app.timepointai.com
                    (timepoint-app SPA)
                           │
                    Auth0 JWT in every request
                           │
                           ▼
                    api.timepointai.com
                    ┌──────────────────┐
                    │ BILLING GATEWAY  │ ← YOU
                    │                  │
                    │ Auth0 verify     │
                    │ Stripe webhooks  │
                    │ API key mgmt    │
                    │ Usage metering   │
                    │ Credit relay     │
                    └──┬───────────┬───┘
                       │           │
              service key    service key
                       │           │
                       ▼           ▼
                    FLASH      CLOCKCHAIN
                 (generate)   (browse/search)
```

---

## 3. What Flash Already Has (Don't Rebuild)

Flash has a **complete credit ledger**. Billing should USE it, not duplicate it:

| Flash Has | How Billing Uses It |
|-----------|---------------------|
| `POST /credits/admin/grant` | Call after Stripe payment to add credits |
| `GET /credits/balance` | Proxy to show user their balance |
| `GET /credits/costs` | Proxy to show pricing |
| `POST /timepoints/generate/sync` | Relay user generation requests |
| `POST /timepoints/generate/stream` | Relay with SSE streaming |
| `PATCH /timepoints/{id}/visibility` | Relay publish requests |
| `X-Service-Key` middleware | Billing authenticates to Flash with this |
| `X-Admin-Key` for grants | Billing uses this to grant credits after payment |
| `TransactionType.STRIPE_PURCHASE` | Flash's ledger already has this enum value |
| `TransactionType.APPLE_IAP` | Flash's ledger already has this enum value |
| `TransactionType.SUBSCRIPTION_GRANT` | Flash's ledger already has this enum value |
| `BILLING_ENABLED` config flag | Flash expects billing to set this |

---

## 4. Auth0 Integration

### Setup

- Auth0 tenant for TIMEPOINT
- **Social connections**: Apple Sign-In (iOS users migrate seamlessly), Google, GitHub, email/password
- **Machine-to-machine (M2M) applications**: for developer API keys
- **API audience**: `https://api.timepointai.com`

### User Flow (app.timepointai.com)

1. User clicks "Sign In" in timepoint-app
2. Auth0 Universal Login opens (or Apple Sign-In on iOS)
3. Auth0 returns JWT to app
4. App sends JWT with every request to `api.timepointai.com`
5. Billing validates JWT, extracts `sub` claim
6. Billing looks up or creates user in Flash (via service key)
7. Billing forwards request to Flash/Clockchain with `X-User-ID: {auth0_sub}`

### Developer Flow (api.timepointai.com)

1. Developer signs up via Auth0
2. Developer creates API key in billing dashboard
3. API key is stored in billing's DB (hashed)
4. Developer sends `Authorization: Bearer {api_key}` with requests
5. Billing validates key, resolves user, meters usage, relays to Flash/Clockchain

### JWT Validation

```python
from authlib.integrations.starlette_client import OAuth
# Or use PyJWT with Auth0's JWKS endpoint

AUTH0_DOMAIN = os.environ["AUTH0_DOMAIN"]
AUTH0_AUDIENCE = os.environ["AUTH0_AUDIENCE"]

async def verify_auth0_token(token: str) -> dict:
    # Validate JWT signature against Auth0 JWKS
    # Verify audience, issuer, expiry
    # Return decoded claims with 'sub' field
    ...
```

---

## 5. Stripe Integration

### Credit Purchases

1. User clicks "Buy Credits" in app
2. App calls `POST /api/v1/billing/checkout` → Billing creates Stripe Checkout session
3. User completes payment on Stripe
4. Stripe sends webhook to `POST /api/v1/billing/webhooks/stripe`
5. Billing verifies webhook signature
6. Billing calls Flash: `POST /credits/admin/grant` with `X-Admin-Key`
7. Flash adds credits to user's ledger with `TransactionType.STRIPE_PURCHASE`

### Subscription Plans (future)

| Plan | Credits/Month | Price | HD Access |
|------|---------------|-------|-----------|
| Free | 0 (browse only) | $0 | No |
| Explorer | 50 | $4.99 | No |
| Historian | 200 | $14.99 | Yes |
| API Pro | 1000 | $49.99 | Yes + API key |

### Apple IAP (iOS)

1. User purchases in iOS app
2. App sends receipt to `POST /api/v1/billing/verify-receipt`
3. Billing validates with Apple's receipt verification API
4. Billing grants credits via Flash's admin endpoint with `TransactionType.APPLE_IAP`

---

## 6. API Key Management

### Developer API Keys

```python
class APIKey(Base):
    __tablename__ = "api_keys"

    id: str           # uuid
    user_id: str      # auth0 sub
    key_hash: str     # sha256 of the key (never store plaintext)
    key_prefix: str   # first 8 chars for display (tp_live_abc12345...)
    name: str         # user-supplied label
    tier: str         # "free" | "pro" | "enterprise"
    rate_limit: int   # requests per minute
    is_active: bool
    created_at: datetime
    last_used_at: datetime
```

### Key Format

```
tp_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4
tp_test_a1b2c3d4e5f6g7h8i9j0k1l2m3n4
```

Prefix `tp_live_` or `tp_test_` for easy identification.

### Rate Limits by Tier

| Tier | RPM | Concurrent | HD Preset | Cost |
|------|-----|------------|-----------|------|
| Free | 10 | 1 | No | $0 |
| Pro | 60 | 5 | Yes | $49/mo |
| Enterprise | 300 | 20 | Yes | Custom |

---

## 7. API Endpoints

### Auth Endpoints

```
POST /api/v1/auth/login
  → Accepts Auth0 JWT, returns session token + user info
  → Creates user in Flash if first login

GET /api/v1/auth/me
  → Current user profile

POST /api/v1/auth/logout
  → Revoke session
```

### Billing Endpoints

```
POST /api/v1/billing/checkout
  → Create Stripe Checkout session for credit purchase
  → Body: { "package": "100_credits" | "500_credits" | ... }
  → Returns: { "checkout_url": "https://checkout.stripe.com/..." }

POST /api/v1/billing/webhooks/stripe
  → Stripe webhook handler (payment completed, subscription events)

POST /api/v1/billing/verify-receipt
  → Apple IAP receipt validation

GET /api/v1/billing/plans
  → Available subscription plans and pricing
```

### Credit Endpoints (proxied to Flash)

```
GET /api/v1/credits/balance
  → Proxy to Flash's /credits/balance

GET /api/v1/credits/history
  → Proxy to Flash's /credits/history

GET /api/v1/credits/costs
  → Proxy to Flash's /credits/costs
```

### API Key Endpoints

```
POST /api/v1/keys
  → Create new API key
  → Returns: { "key": "tp_live_...", "prefix": "tp_live_a1b2" }
  → Key shown ONCE, then only prefix stored

GET /api/v1/keys
  → List user's API keys (prefix + name + usage stats)

DELETE /api/v1/keys/{key_id}
  → Revoke an API key

GET /api/v1/keys/{key_id}/usage
  → Usage statistics for a key
```

### Generation Relay (proxied to Flash)

```
POST /api/v1/generate
  → Verify auth → check credits → relay to Flash
  → Returns Flash's response

POST /api/v1/generate/stream
  → Same but with SSE streaming passthrough

GET /api/v1/timepoints/{id}
  → Proxy to Flash
```

### Clockchain Relay (proxied to Clockchain)

```
GET /api/v1/moments/{path}
  → Proxy to Clockchain's browse API

GET /api/v1/browse/{path}
  → Proxy to Clockchain

GET /api/v1/today
  → Proxy to Clockchain

GET /api/v1/search?q={query}
  → Proxy to Clockchain

GET /api/v1/graph/neighbors/{id}
  → Proxy to Clockchain
```

---

## 8. Usage Metering

Track every API call:

```python
class UsageRecord(Base):
    __tablename__ = "usage_records"

    id: str
    user_id: str
    api_key_id: str | None    # null for session-based access
    endpoint: str             # e.g., "/api/v1/generate"
    method: str               # GET, POST
    status_code: int
    credits_spent: int        # 0 for reads, N for generation
    response_time_ms: int
    preset: str | None        # for generation requests
    created_at: datetime
```

Aggregate daily/monthly for billing dashboards and rate limit enforcement.

---

## 9. Tech Stack

- **Framework:** FastAPI (consistent with Flash and Clockchain)
- **Auth:** Auth0 (authlib or PyJWT + JWKS)
- **Payments:** Stripe Python SDK
- **Database:** PostgreSQL (user records, API keys, usage — NOT credits, those are in Flash)
- **Deployment:** Railway (Docker)
- **Python 3.11+**

### Env Vars

```bash
# Auth0
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_AUDIENCE=https://api.timepointai.com
AUTH0_CLIENT_ID=...
AUTH0_CLIENT_SECRET=...

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_100_CREDITS=price_...
STRIPE_PRICE_500_CREDITS=price_...

# Internal services
FLASH_URL=https://timepoint-flash-deploy-production.up.railway.app
FLASH_SERVICE_KEY=...          # same key Flash expects
FLASH_ADMIN_KEY=...            # Flash's ADMIN_API_KEY
CLOCKCHAIN_URL=https://...     # Clockchain's Railway URL
CLOCKCHAIN_SERVICE_KEY=...     # Clockchain's service key

# Billing DB
DATABASE_URL=postgresql+asyncpg://...

# Application
ENVIRONMENT=production
```

---

## 10. Project Structure

```
timepoint-billing/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI, CORS, middleware
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py           # /auth/login, /auth/me, /auth/logout
│   │   ├── billing.py        # /billing/checkout, webhooks, verify-receipt
│   │   ├── keys.py           # /keys CRUD
│   │   ├── credits.py        # Proxy to Flash /credits/*
│   │   ├── generate.py       # Proxy to Flash /timepoints/generate
│   │   └── clockchain.py     # Proxy to Clockchain browse/search
│   ├── core/
│   │   ├── __init__.py
│   │   ├── auth0.py          # Auth0 JWT validation
│   │   ├── stripe_client.py  # Stripe integration
│   │   ├── flash_client.py   # httpx client for Flash
│   │   ├── clockchain_client.py  # httpx client for Clockchain
│   │   ├── api_keys.py       # Key generation, hashing, validation
│   │   ├── metering.py       # Usage tracking
│   │   └── config.py         # Settings
│   └── models/
│       ├── __init__.py
│       ├── db.py             # SQLAlchemy models (APIKey, UsageRecord)
│       └── schemas.py        # Pydantic models
├── tests/
├── Dockerfile
├── railway.json
├── requirements.txt
└── README.md
```

---

## 11. CORS

Billing IS browser-facing (api.timepointai.com). Set CORS:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.timepointai.com",
        "https://timepointai.com",
    ],
    allow_origin_regex=r"http://localhost:\d+",
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
    allow_credentials=True,
)
```

---

## 12. Key Design Decisions

1. **Billing is a thin gateway** — does NOT duplicate Flash's credit ledger
2. **Auth0 for identity** — supports Apple Sign-In (iOS) + web login + M2M
3. **Stripe for payments** — credit purchases and subscriptions
4. **API keys managed here** — not in Flash or Clockchain
5. **Usage metering here** — not in Flash or Clockchain
6. **Credits live in Flash** — billing calls Flash's admin grant after payment
7. **PostgreSQL** — needs relational storage for keys, usage, billing records
8. **FastAPI** — consistent with all services
9. **Railway** — consistent deployment

---

## 13. What Success Looks Like

### Phase 1 (Build Now)
- [ ] FastAPI on Railway with health check
- [ ] Auth0 JWT validation working
- [ ] Proxy browse requests to Clockchain
- [ ] Proxy generation requests to Flash (with service key)
- [ ] Credit balance/costs proxied from Flash
- [ ] CORS for app.timepointai.com

### Phase 2 (Monetization)
- [ ] Stripe Checkout for credit purchases
- [ ] Stripe webhook handling
- [ ] API key CRUD
- [ ] Usage metering per key
- [ ] Rate limiting per tier
- [ ] Apple IAP receipt validation

### Phase 3 (Scale)
- [ ] Subscription plans
- [ ] Usage dashboards
- [ ] Developer portal / docs
- [ ] Billing admin panel

---

## 14. Services Reference

| Service | Repo | Domain | Status |
|---------|------|--------|--------|
| Landing | timepoint-landing | `timepointai.com` | Live |
| Flash | timepoint-flash-deploy | *(internal)* | Live |
| Clockchain | timepoint-clockchain | *(internal)* | Building |
| App | timepoint-app | `app.timepointai.com` | Planned |
| Billing | timepoint-billing | `api.timepointai.com` | **BUILD THIS** |

---

**TIMEPOINT · Synthetic Time Travel™**

*"Billing is the front door. It decides who gets in, what they can touch, and what it costs. Everything behind it — Flash, Clockchain — just does the work."*
