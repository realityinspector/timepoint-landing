# HANDOFF MEMO: timepoint-clockchain Agent
**From:** timepoint-landing · Feb 2026
**Re:** Build the Clockchain — TIMEPOINT's autonomous temporal index and orchestration service

---

## 1. What You Are Building

The **Clockchain** is a new microservice: TIMEPOINT's **spatiotemporal graph index and autonomous content orchestrator**. It maintains an ever-growing graph of moments in history, orchestrates scene generation by dispatching jobs to Flash, and serves browse/search data to the TIMEPOINT app.

**The Clockchain does three things:**

1. **Maintains a graph index** (NetworkX) of every catalogued moment — organized by canonical temporal URLs
2. **Orchestrates scene generation** by deciding what to render, queuing jobs, and dispatching them to Flash
3. **Serves browse/search/discovery data** to `timepoint-app` and `timepoint-billing`

This is a **lightweight implementation** — NOT the full decentralized protocol from Sean's May 2022 blog post (https://clockchain.notion.site). You're building the pragmatic first step: a persistent autonomous agent populating an ever-expanding temporal library.

---

## 2. Full Platform Architecture

### The 5-Service Map

| Domain | Repo | Purpose | Public? |
|--------|------|---------|---------|
| `timepointai.com` | timepoint-landing | Marketing landing page, static HTML | Yes (no auth) |
| `app.timepointai.com` | timepoint-app (NEW) | Frontend SPA — browse + render | Yes (Auth0 login) |
| `api.timepointai.com` | timepoint-billing (NEW) | Auth0, Stripe, API keys, metered relay | Yes (JWT / API keys) |
| *(internal)* | timepoint-flash | Credit ledger, generation, interactions | No — called by billing + clockchain |
| *(internal)* | timepoint-clockchain (NEW) | Graph index, autonomous workers | No — called by app + billing |

### What Already Exists in Flash

Flash is mature (630+ tests). It **already has**:
- **Auth**: Apple Sign-In + JWT (Auth0 being added via timepoint-billing)
- **Credit ledger**: Immutable transaction log, per-operation costs, admin grants
- **Billing hooks**: `BILLING_ENABLED` flag, `TransactionType` enum with `STRIPE_PURCHASE`, `APPLE_IAP`, `SUBSCRIPTION_GRANT`, `REFUND`
- **Service key middleware**: `X-Service-Key` header, `X-Admin-Key` for privileged ops
- **Public/private visibility**: On the Timepoint model
- **Generation**: Streaming SSE, 4 presets (hd/balanced/hyper/gemini3)
- **Character interactions**: Chat, dialog, surveys
- **Temporal navigation**: Jump forward/backward in time
- **Slug generation**: Auto-generated from query

**Clockchain does NOT replicate any of this.** Auth and credits live in Flash (managed via billing). Clockchain is the graph engine and autonomous operator.

### Data Flow

```
┌────────────────────────────────────────────────────────────────────┐
│                          PUBLIC SURFACE                            │
│                                                                    │
│  timepointai.com        app.timepointai.com    api.timepointai.com │
│  (landing)              (app SPA)              (billing gateway)   │
│  Static HTML            Auth0 login            Auth0 / API keys   │
│  No API calls           Browse + render        Stripe, metering   │
└─────────────────────────┬───────────────────────┬──────────────────┘
                          │                       │
                   browse + search          relay + meter
                          │                       │
┌─────────────────────────▼───────────────────────▼──────────────────┐
│                        INTERNAL SERVICES                           │
│                                                                    │
│  timepoint-clockchain ─────────────────► timepoint-flash           │
│  (graph + workers)      workers call     (credit ledger + render)  │
│                         Flash to                                   │
│  Browse/search API      generate scenes  Called by billing +       │
│  Graph expansion                         clockchain only           │
│  "Today in History"                                                │
└────────────────────────────────────────────────────────────────────┘
```

### Who Calls Whom

| Caller | Calls | Purpose | Auth |
|--------|-------|---------|------|
| timepoint-app | Clockchain | Browse graph, search, today-in-history | `X-Service-Key` |
| timepoint-app | timepoint-billing | Generate scenes, auth, buy credits | Auth0 JWT |
| timepoint-billing | Flash | Relay generation + credit ops | `X-Service-Key` + `X-Admin-Key` |
| timepoint-billing | Clockchain | Fetch graph data for API consumers | `X-Service-Key` |
| Clockchain workers | Flash | Autonomous scene generation (unmetered) | `X-Service-Key` |

### Auth Architecture

- **Auth0** — identity provider shared by app and billing (supports Apple Sign-In as social connection + email/Google/GitHub for web)
- **timepoint-billing** — validates Auth0 JWTs, manages API keys, handles Stripe, forwards identity to Flash
- **Flash** — trusts forwarded `X-User-ID` from billing; owns credit ledger, spend/grant ops
- **Clockchain** — trusts `X-Service-Key` from app and billing; does NOT validate users or handle credits
- **Service keys** (shared secrets via env vars) for all service-to-service calls

---

## 3. Public vs Private Timepoints

### How It Works

Flash already has `visibility: PUBLIC | PRIVATE` on its Timepoint model.

**Public Timepoints**
- Generated autonomously by Clockchain workers → stored in Flash as `PUBLIC`
- **Free to browse** in the app (Layer 0-1 without login, full scenes with free login)
- The ever-growing library — Clockchain generates these 24/7

**Private Timepoints**
- User-requested via the app → billing verifies credits → Flash generates as `PRIVATE`
- Only visible to the requesting user
- User can **publish** → becomes public, Clockchain indexes it
- Publishing enriches the library for everyone

### Clockchain's Role

Clockchain maintains the **graph index** of all public timepoints (and references to private ones for their owners). It does NOT store scene content — Flash does. Clockchain stores:
- **Layer 0**: URL path + event name (graph node)
- **Layer 1**: Metadata — figures, tags, one-liner, sources (node attributes)
- **Layer 2 reference**: `flash_timepoint_id` pointing to Flash's DB (not the scene itself)

When a user requests a moment:
1. App checks Clockchain: does this path exist?
2. If yes (Layer 2): app fetches full scene from Flash by `flash_timepoint_id`
3. If yes (Layer 0-1 only): app shows metadata, offers to generate (costs credits via billing)
4. If no: app sends request through billing → Flash generates → Clockchain indexes result

---

## 4. Canonical URL Format

```
/{year}/{month}/{day}/{time}/{country}/{region}/{city}/{slug}
```

### Format Rules

| Segment | Format | Examples |
|---------|--------|----------|
| `year` | Integer, negative for BCE | `1969`, `-44`, `2001` |
| `month` | Spelled out, lowercase | `march`, `november`, `july` |
| `day` | Integer, no zero-padding | `15`, `1`, `28` |
| `time` | 24hr, no colon | `1030`, `0900`, `2300` |
| `country` | Modern borders, lowercase | `italy`, `united-states`, `japan` |
| `region` | State/province/region | `lazio`, `new-mexico`, `texas` |
| `city` | City/locality | `rome`, `los-alamos`, `dallas` |
| `slug` | Auto-generated, kebab-case | `assassination-of-julius-caesar` |

### Example URLs

```
/-44/march/15/1030/italy/lazio/rome/assassination-of-julius-caesar
/1945/july/16/0530/united-states/new-mexico/socorro/trinity-test
/1969/november/14/1122/united-states/florida/cape-canaveral/apollo-12-lightning-launch
/2016/march/9/1530/south-korea/seoul/seoul/alphago-move-37
```

### URL Hierarchy Browsing

Partial paths return listings:
- `/1969` → all events in 1969
- `/1969/july` → all events in July 1969
- `/1969/july/20` → all events on July 20, 1969

---

## 5. Variable-Depth Content Layers

| Layer | Name | Stored In | Content | Generation |
|-------|------|-----------|---------|------------|
| 0 | **Slug** | Clockchain graph | URL path + event name | Bulk (LLM expansion) |
| 1 | **Metadata** | Clockchain graph | Date, location, figures, one-liner, sources, tags | Bulk or on-demand |
| 2 | **Flash Scene** | Flash DB | Full narrative, image, characters, dialog | On-demand via Flash |
| 3 | **Daedalus Sim** | Future | SNAG social graph, agent interactions | Future |
| 4 | **Interactive** | Future | Fine-tuned models, counterfactuals | Future |

Millions of Layer 0 nodes (cheap). Thousands with Layer 2 scenes. Layer 0-1 makes the graph browsable before scenes exist.

### Layer Access by Tier

| Layer | No login | Free (logged in) | Freemium (credits) | Paid API |
|-------|----------|-------------------|---------------------|----------|
| 0-1 | Browse | Browse | Browse | Full access |
| 2 | Preview | Full read (public) | Generate new (private) | Full + HD preset |
| 3+ | — | — | Future | Future |

---

## 6. Tech Stack

- **Framework:** FastAPI
- **Graph:** NetworkX — in-memory, serialized to disk as JSON
- **Queue:** In-process asyncio queue (graduate to Redis if needed)
- **Storage:** Filesystem JSON (graduate to SQLite → Postgres if needed)
- **Deployment:** Railway (Docker)
- **Python 3.11+**

### Railway Config

```json
{
  "$schema": "https://railway.com/railway.schema.json",
  "build": { "builder": "DOCKERFILE", "dockerfilePath": "Dockerfile" },
  "deploy": {
    "healthcheckPath": "/health",
    "healthcheckTimeout": 30,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

---

## 7. The Graph (NetworkX)

### Node Schema

```python
G.add_node("/-44/march/15/1030/italy/lazio/rome/assassination-of-julius-caesar", **{
    "type": "event",
    "name": "Assassination of Julius Caesar",
    "year": -44,
    "month": "march",
    "day": 15,
    "time": "1030",
    "country": "italy",
    "region": "lazio",
    "city": "rome",
    "slug": "assassination-of-julius-caesar",
    "layer": 2,
    "visibility": "public",
    "created_by": "system",
    "tags": ["politics", "ancient-rome", "assassination"],
    "one_liner": "Senators assassinate dictator Julius Caesar on the Ides of March",
    "figures": ["Julius Caesar", "Marcus Brutus", "Gaius Cassius"],
    "flash_timepoint_id": "uuid-from-flash",  # null if Layer < 2
    "created_at": "2026-02-17T00:00:00Z",
})
```

Clockchain stores metadata + Flash reference. Full scene content lives in Flash's DB.

### Edge Types

```python
G.add_edge(caesar_node, civil_war_node, type="causes", weight=0.95)
G.add_edge(event_a, event_b, type="contemporaneous")
G.add_edge(event_a, event_b, type="same_location")
G.add_edge(event_a, event_b, type="thematic", theme="assassinations")
```

### Bulk Slug Generation

1. Start with seed events (~500 notable moments)
2. LLM generates related events per seed (causes, effects, contemporaneous, thematic)
3. Build graph outward — each new node links to what generated it
4. Serialize to disk periodically
5. Runs as background worker, expanding autonomously

---

## 8. API Endpoints

### Browse API (called by timepoint-app and timepoint-billing)

Auth: `X-Service-Key` header.

```
GET /api/v1/moments/{full_temporal_path}
  → Moment metadata from graph
  → If Layer 2: includes flash_timepoint_id (caller fetches scene from Flash)
  → Public only (unless user_id forwarded for private)

GET /api/v1/browse/{partial_path}
  → Listing of child nodes, public only, paginated

GET /api/v1/today
  → Moments on this date in history (public)

GET /api/v1/random
  → Random public moment (Layer 1+)

GET /api/v1/search?q={query}
  → Full-text search across names, descriptions, figures, tags

GET /api/v1/graph/neighbors/{node_id}
  → Connected nodes (causes, effects, related)

GET /api/v1/stats
  → Total nodes per layer, edges, coverage
```

### Indexing API (called after Flash generates a scene)

```
POST /api/v1/index
  → Add or update a moment in the graph
  → Body: {
      "path": "/-44/march/15/...",
      "flash_timepoint_id": "uuid",
      "metadata": { name, figures, tags, one_liner, ... },
      "visibility": "public" | "private",
      "created_by": "system" | "user:{user_id}"
    }

POST /api/v1/publish/{path}
  → Set visibility "public" on a private node
```

### Worker Management (admin only)

```
POST /api/v1/expand
  → Trigger graph expansion from a seed
  → Body: { "seed": "Roman Republic", "depth": 2, "max_nodes": 100 }

GET /api/v1/jobs/{job_id}
  → Poll worker job status
```

---

## 9. Autonomous Workers

### Worker 1: Graph Expander (cron)

- Runs on schedule (every N hours, or continuously with rate limiting)
- Picks frontier nodes (Layer 0, few connections)
- LLM generates related events
- Adds new Layer 0/1 nodes — `visibility: "public"`, `created_by: "system"`
- Serializes graph to disk

### Worker 2: Scene Renderer (queue)

- Watches job queue for moments to promote to Layer 2
- Calls Flash: `POST /api/v1/timepoints/generate/sync` with `X-Service-Key`
- No credits deducted (system generation, no user context)
- Stores `flash_timepoint_id` back in graph node
- n parallel workers (start with 2-3), handles retries

### Worker 3: "Today in History" (daily cron)

- Midnight UTC: identify events matching today's month+day
- Ensure Layer 1 data exists for top 10-20
- Queue top 3-5 for Layer 2 generation via Flash
- Pre-rendered so `/api/v1/today` returns rich content

### Worker 4: LLM Content Judge

- Screens requests BEFORE dispatching to Flash
- Three tiers:
  - **Innocuous** → auto-approve
  - **Sensitive** (violence, controversial) → generate with disclaimer
  - **Reject** (harmful) → error, don't generate
- Lightweight LLM call (Haiku or similar)
- Saves Flash compute on rejected content

---

## 10. Flash Integration

**Flash is live** at `https://timepoint-flash-deploy-production.up.railway.app`

### Flash Endpoints Clockchain Uses

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/timepoints/generate/sync` | Generate scene (service key, no credits) |
| `GET /api/v1/timepoints/{id}` | Fetch scene by ID |
| `GET /api/v1/timepoints/slug/{slug}` | Lookup by slug |
| `PATCH /api/v1/timepoints/{id}/visibility` | Set public/private |

### Calling Flash

```python
import httpx
import os

FLASH_URL = os.environ["FLASH_URL"]
FLASH_KEY = os.environ["FLASH_SERVICE_KEY"]

async def generate_scene(query: str, preset: str = "balanced") -> dict:
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{FLASH_URL}/api/v1/timepoints/generate/sync",
            json={"query": query, "preset": preset},
            headers={"X-Service-Key": FLASH_KEY},
        )
        return response.json()
```

### After Flash Generates

1. Extract `id` → store as `flash_timepoint_id` in graph node
2. Extract metadata (year, location, slug) → enrich Layer 1
3. Add causal/thematic edges if scene references known events
4. Update node `layer` to 2
5. Serialize graph

---

## 11. Service Key Auth

### Inbound (callers → Clockchain)

```
X-Service-Key: {CLOCKCHAIN_SERVICE_KEY}
```

Set as Railway env var. Share with `timepoint-app` and `timepoint-billing`.

Optional user identity forwarding:
```
X-User-ID: auth0|abc123
```

Clockchain trusts forwarded identity. Auth0 validation happens in billing, not here.

### Outbound (Clockchain → Flash)

```
X-Service-Key: {FLASH_SERVICE_KEY}
```

### No CORS

Clockchain is never called from browsers. App and billing backends proxy all requests.

---

## 12. Data Persistence

### MVP: Filesystem

```
data/
  graph.json              # NetworkX graph as node-link JSON
  jobs/
    {job_id}.json          # Worker job status
```

Scene content lives in Flash's DB, not here. Clockchain stores graph topology + Layer 0/1 metadata + Flash ID references.

### Graduation Path

1. SQLite + FTS5 for search
2. Postgres
3. NetworkX stays as in-memory cache

---

## 13. Seed Data

| Event | Path |
|-------|------|
| Assassination of Caesar | `/-44/march/15/1030/italy/lazio/rome/assassination-of-julius-caesar` |
| Trinity Test | `/1945/july/16/0530/united-states/new-mexico/socorro/trinity-test` |
| Apollo 12 Lightning Launch | `/1969/november/14/1122/united-states/florida/cape-canaveral/apollo-12-lightning-launch` |
| AlphaGo Move 37 | `/2016/march/9/1530/south-korea/seoul/seoul/alphago-move-37` |
| Moon Landing | `/1969/july/20/2056/united-states/florida/cape-canaveral/apollo-11-moon-landing` |

All: `visibility: "public"`, `created_by: "system"`.

---

## 14. Project Structure

```
timepoint-clockchain/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI, startup, service key middleware
│   ├── api/
│   │   ├── __init__.py
│   │   ├── moments.py       # /moments, /browse, /today, /random, /search
│   │   ├── index.py         # /index, /publish
│   │   └── graph.py         # /graph/neighbors, /stats, /expand
│   ├── core/
│   │   ├── __init__.py
│   │   ├── graph.py          # NetworkX graph manager
│   │   ├── url.py            # Canonical URL parsing/building
│   │   ├── auth.py           # Service key validation
│   │   └── config.py         # Settings, env vars
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── expander.py       # Graph expansion
│   │   ├── renderer.py       # Flash dispatch
│   │   ├── daily.py          # "Today in History" cron
│   │   └── judge.py          # LLM content moderation
│   └── models/
│       ├── __init__.py
│       └── schemas.py        # Pydantic models
├── data/
│   ├── seeds.json
│   └── .gitkeep
├── tests/
├── Dockerfile
├── railway.json
├── requirements.txt
└── README.md
```

---

## 15. Key Design Decisions (Already Made)

1. **Months spelled out** in URLs — `march` not `03`
2. **Modern geography** — even for ancient events
3. **Auto-generated slugs**
4. **NetworkX** for the graph
5. **Flash owns the credit ledger** — Clockchain never handles credits
6. **timepoint-billing owns auth** (Auth0, Stripe, API keys) — Clockchain trusts service keys
7. **5-service architecture** — landing, app, billing, clockchain, flash
8. **LLM judge before Flash** — saves compute
9. **Start simple** — asyncio queue, filesystem, in-memory graph
10. **Railway** for deployment
11. **FastAPI** — consistent with Flash
12. **Public timepoints are free** — auto-generated by workers
13. **Private timepoints cost credits** — managed by Flash's ledger via billing
14. **Scene content in Flash's DB** — Clockchain stores references only

---

## 16. What Success Looks Like

### Phase 1 (Build Now)
- [ ] FastAPI service on Railway with health check
- [ ] Service key middleware
- [ ] NetworkX graph with 5 seed events (Layer 0-1)
- [ ] `GET /api/v1/moments/{path}` returns seed data
- [ ] `GET /api/v1/browse/{partial_path}` returns listings
- [ ] `GET /api/v1/today` returns today-in-history
- [ ] Scene Renderer worker: calls Flash, stores `flash_timepoint_id`
- [ ] Graph Expander worker: adds related events around seeds
- [ ] `POST /api/v1/index` accepts new moments
- [ ] Public/private visibility on all nodes
- [ ] Graph serialized to disk, survives restarts

### Phase 2 (After app + billing exist)
- [ ] LLM content judge
- [ ] "Today in History" daily cron
- [ ] 1000+ Layer 0 nodes
- [ ] 50+ Layer 2 scenes
- [ ] Search endpoint
- [ ] Publish endpoint (private → public)

### Phase 3 (Future)
- [ ] Daedalus (Layer 3) integration
- [ ] Semantic search
- [ ] Graph visualization API

---

## 17. Existing Services

| Service | Repo | Domain | Status |
|---------|------|--------|--------|
| Landing | timepoint-landing | `timepointai.com` | Live |
| Flash | timepoint-flash-deploy | *(internal)* | Live |
| Clockchain | timepoint-clockchain | *(internal)* | **BUILD THIS** |
| App | timepoint-app | `app.timepointai.com` | Planned |
| Billing | timepoint-billing | `api.timepointai.com` | Planned |

---

**TIMEPOINT · Synthetic Time Travel™**

*"Flash renders moments. The Clockchain remembers all of them, connects them, and decides which ones to illuminate next. Billing opens the door. The App is the window."*
