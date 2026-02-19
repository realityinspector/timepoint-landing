# HANDOFF MEMO: timepoint-clockchain Agent
**From:** timepoint-landing · Feb 2026
**Re:** The Clockchain — TIMEPOINT's spatiotemporal graph index and autonomous content orchestrator

---

## 1. What You Built

The **Clockchain** is TIMEPOINT's **spatiotemporal graph index and autonomous content orchestrator**. It maintains an ever-growing graph of moments in history, orchestrates scene generation by dispatching jobs to Flash, and serves browse/search data.

**The Clockchain does three things:**

1. **Maintains a graph index** (NetworkX) of every catalogued moment — organized by canonical temporal URLs
2. **Orchestrates scene generation** by deciding what to render, queuing jobs, and dispatching them to Flash
3. **Serves browse/search/discovery data** via its API

**Status: Fully built and deployed.** 6 commits, 11 test files, all Phase 1 + Phase 2 features complete.

---

## 2. Full Platform Architecture (As Built)

### The 5-Service Map

| Domain | Repo | Purpose | Public? |
|--------|------|---------|---------|
| `timepointai.com` | timepoint-landing | Marketing landing page, static HTML | Yes (no auth) |
| `app.timepointai.com` | timepoint-app (NEW) | Frontend SPA — browse + render | Yes (Auth0 login) |
| `api.timepointai.com` | timepoint-flash-deploy | THE GATEWAY: auth, credits, generation, proxies | Yes (JWT / API keys) |
| *(internal)* | timepoint-billing | Stripe, Apple IAP, subscriptions | No — called by flash-deploy |
| *(internal)* | timepoint-clockchain | Graph index, autonomous workers | No — needs proxy in flash-deploy |

### What Already Exists in Flash

Flash-deploy is the unified gateway (630+ tests). All billing integration points are **live and deployed**:
- **Three auth paths**: Service key + X-User-ID (billing relay), service key only (Clockchain workers), Bearer JWT (direct)
- **User resolution**: `POST /users/resolve` — find-or-create by `external_id` (Auth0 sub), auto-provisions credits
- **Credit ledger**: Immutable transaction log, per-operation costs, admin grants with `transaction_type` param
- **Callback URLs**: Generate endpoints accept `callback_url` + `request_context` for async workflows
- **Service key middleware**: `X-Service-Key` header, `X-Admin-Key` for privileged ops
- **Public/private visibility**: On the Timepoint model
- **Billing proxy**: `/api/v1/billing/*` → billing microservice
- **Generation**: Streaming SSE, 4 presets (hd/balanced/hyper/gemini3)

**Clockchain does NOT replicate any of this.** Auth and credits live in Flash (managed via billing). Clockchain is the graph engine and autonomous operator.

### Data Flow

```
┌────────────────────────────────────────────────────────────────────┐
│                          PUBLIC SURFACE                            │
│                                                                    │
│  timepointai.com        app.timepointai.com    api.timepointai.com │
│  (landing)              (app SPA)              (flash-deploy)      │
│  Static HTML            Auth0 login            THE GATEWAY         │
│  No API calls           Browse + render        Auth, credits, gen  │
└─────────────────────────┬───────────────────────┬──────────────────┘
                          │                       │
                    all requests           proxies billing
                    go here                + clockchain (*)
                          │                       │
                          ▼                       │
                    flash-deploy ─────────────────┤
                    (api.timepointai.com)          │
                          │                       │
                          │              ┌────────┴────────┐
                          │              │                 │
                          ▼              ▼                 ▼
                    generation      billing (internal)  clockchain
                    (built-in)      (Stripe, Apple)     (graph, search)
```

(*) **Clockchain proxy needs to be built in flash-deploy** — see Section 17.

### Who Calls Whom

| Caller | Calls | Purpose | Auth |
|--------|-------|---------|------|
| timepoint-app | flash-deploy | Everything (via single API) | JWT |
| flash-deploy | Clockchain | Proxy browse/search requests (*) | `X-Service-Key` |
| flash-deploy | Billing | Proxy payment requests | `X-Service-Key` |
| Billing | Flash-deploy | Grant credits after payment | `X-Service-Key` + `X-Admin-Key` |
| Clockchain workers | Flash-deploy | Autonomous scene generation (unmetered) | `X-Service-Key` |

### Auth Architecture

- **Auth0** (planned) — identity provider for web app. Flash-deploy already has `external_id` and `/users/resolve` ready.
- **Apple Sign-In** — current JWT auth in flash-deploy (iOS)
- **flash-deploy** — validates JWTs, manages service keys, handles auth flows
- **Flash** — trusts forwarded `X-User-ID`; owns credit ledger, spend/grant ops
- **Clockchain** — trusts `X-Service-Key` from flash-deploy; does NOT validate users or handle credits
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
- User-requested via the app → flash-deploy verifies credits → Flash generates as `PRIVATE`
- Only visible to the requesting user
- User can **publish** → becomes public, Clockchain indexes it
- Publishing enriches the library for everyone

### Clockchain's Role

Clockchain maintains the **graph index** of all public timepoints (and references to private ones for their owners). It does NOT store scene content — Flash does. Clockchain stores:
- **Layer 0**: URL path + event name (graph node)
- **Layer 1**: Metadata — figures, tags, one-liner, sources (node attributes)
- **Layer 2 reference**: `flash_timepoint_id` pointing to Flash's DB (not the scene itself)

When a user requests a moment:
1. App checks Clockchain (via flash-deploy proxy): does this path exist?
2. If yes (Layer 2): app fetches full scene from Flash by `flash_timepoint_id`
3. If yes (Layer 0-1 only): app shows metadata, offers to generate (costs credits)
4. If no: app sends request through flash-deploy → Flash generates → Clockchain indexes result

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

---

## 6. What's Built (Complete)

### Tech Stack
- **Framework:** FastAPI
- **Graph:** NetworkX — in-memory, serialized to disk as JSON (`nx.node_link_data()`)
- **Queue:** In-process asyncio (background tasks)
- **Storage:** Filesystem JSON (`data/graph.json`, `data/scenes/{path}/scene.json`)
- **Deployment:** Railway (Docker)
- **Python 3.11+**
- **Dependencies:** fastapi, uvicorn, pydantic, pydantic-settings, httpx, networkx, google-genai

### API Endpoints (All Built)

Auth: `X-Service-Key` header on all endpoints.

**Browse & Discovery:**
```
GET /health                              → Graph stats (no auth)
GET /api/v1/browse                       → Root year segments
GET /api/v1/browse/{path}                → Hierarchical browsing
GET /api/v1/moments/{path}               → Full moment data + edges
GET /api/v1/today                        → Events matching today's date
GET /api/v1/random                       → Random public moment (Layer 1+)
GET /api/v1/search?q={query}             → Full-text search with scoring
```

**Graph:**
```
GET /api/v1/graph/neighbors/{path}       → Connected nodes + edge metadata
GET /api/v1/stats                        → Total nodes/edges, layer/edge-type counts
```

**Generation & Indexing:**
```
POST /api/v1/generate                    → Queue scene generation (+ content judge)
GET  /api/v1/jobs/{job_id}               → Poll job status
POST /api/v1/moments/{path}/publish      → Set visibility to public
POST /api/v1/bulk-generate               → Batch generation (admin key)
POST /api/v1/index                       → Manually add/update node in graph
```

### Workers (All Built, Feature-Gated)

1. **Graph Expander** (`EXPANSION_ENABLED=true` + `GOOGLE_API_KEY`) — Gemini 2.0 Flash generates related events for frontier nodes every 300s
2. **Content Judge** (`GOOGLE_API_KEY`) — Gemini-based screening: approve/sensitive/reject
3. **Daily Worker** (`DAILY_CRON_ENABLED=true`) — "Today in History" auto-generation, runs every 24h
4. **Flash Client** — async httpx client to flash-deploy for scene generation with `request_context`

### Graph (NetworkX)

Nodes keyed by canonical path. Auto-linking on add:
- **Contemporaneous**: same year ±1 (weight=0.5)
- **Same location**: matching country/region/city (weight=0.5)
- **Thematic**: overlapping tags (weight=0.3)
- **Causal**: manual edge type

### Seed Data (5 events)

| Event | Path |
|-------|------|
| Assassination of Caesar | `/-44/march/15/1030/italy/lazio/rome/assassination-of-julius-caesar` |
| Trinity Test | `/1945/july/16/0530/united-states/new-mexico/socorro/trinity-test` |
| Apollo 12 Lightning Launch | `/1969/november/14/1122/united-states/florida/cape-canaveral/apollo-12-lightning-launch` |
| Apollo 11 Moon Landing | `/1969/july/20/2056/united-states/florida/cape-canaveral/apollo-11-moon-landing` |
| AlphaGo Move 37 | `/2016/march/9/1530/south-korea/seoul/seoul/alphago-move-37` |

Pre-configured edges: Apollo 11 ↔ Apollo 12 (contemporaneous), Trinity → Apollo 11 (causal).

---

## 7. Project Structure (As Built)

```
timepoint-clockchain/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI, lifespan, health, workers startup
│   ├── api/
│   │   ├── __init__.py      # api_router combines all routes
│   │   ├── moments.py       # /moments, /browse, /today, /random, /search
│   │   ├── generate.py      # /generate, /jobs, /publish, /bulk-generate, /index
│   │   └── graph.py         # /graph/neighbors, /stats
│   ├── core/
│   │   ├── __init__.py
│   │   ├── graph.py          # GraphManager (NetworkX, auto-linking, persistence)
│   │   ├── jobs.py           # JobManager (create, process, Flash dispatch)
│   │   ├── url.py            # Canonical URL parsing/building, slugification
│   │   ├── auth.py           # Service key validation, user ID extraction
│   │   └── config.py         # Settings (pydantic-settings)
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── renderer.py       # FlashClient (httpx async)
│   │   ├── expander.py       # GraphExpander (Gemini, autonomous)
│   │   ├── judge.py          # ContentJudge (Gemini, approve/reject)
│   │   └── daily.py          # DailyWorker ("Today in History" cron)
│   └── models/
│       ├── __init__.py
│       └── schemas.py        # Pydantic request/response models
├── data/
│   ├── seeds.json            # 5 seed events
│   └── graph.json            # Persisted graph (auto-created)
├── tests/                    # 11 test files
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_integration.py   # Full end-to-end workflow
│   ├── test_api_moments.py
│   ├── test_generate.py
│   ├── test_graph.py
│   ├── test_edges.py
│   ├── test_url.py
│   ├── test_expander.py
│   ├── test_judge.py
│   └── test_daily.py
├── docs/
│   └── UPDATE-FROM-FLASH.md
├── Dockerfile
├── pyproject.toml
├── .env.example
└── README.md
```

---

## 8. Env Vars

```bash
SERVICE_API_KEY=your-service-key-here
FLASH_URL=http://timepoint-flash-deploy.railway.internal:8080
FLASH_SERVICE_KEY=your-flash-service-key-here
DATA_DIR=./data
ENVIRONMENT=development
DEBUG=false
PORT=8080
GOOGLE_API_KEY=                          # Optional (enables judge + expander)
EXPANSION_ENABLED=false                  # Graph expander worker
DAILY_CRON_ENABLED=false                 # "Today in History" worker
ADMIN_KEY=                               # For bulk-generate
```

---

## 9. Git History

```
3ff625d Fix volume permissions for Railway deployment
d52a42a Add Railway volume support for persistent graph data
d3b463c Fix Flash integration for live deployment
e8c5fdf docs: add UPDATE-FROM-FLASH memo confirming Flash compatibility
3b0138e start clockchain
5cca36b Initial commit
```

---

## 10. Key Design Decisions (Implemented)

1. **Months spelled out** in URLs — `march` not `03`
2. **Modern geography** — even for ancient events
3. **Auto-generated slugs**
4. **NetworkX** for the graph (in-memory + JSON persistence)
5. **Flash owns the credit ledger** — Clockchain never handles credits
6. **Flash-deploy is the gateway** — validates auth, proxies clockchain requests
7. **5-service architecture** — landing, app, flash-deploy, billing, clockchain
8. **LLM judge before Flash** — saves compute
9. **Feature-gated workers** — expander and daily cron are opt-in
10. **Railway** for deployment with volume persistence
11. **FastAPI** — consistent with Flash
12. **Public timepoints are free** — auto-generated by workers
13. **Private timepoints cost credits** — managed by Flash's ledger
14. **Scene content in Flash's DB** — Clockchain stores references only
15. **Auto-linking** — contemporaneous, same-location, and thematic edges created automatically

---

## 11. Completion Status

### Phase 1 (Done)
- [x] FastAPI service on Railway with health check
- [x] Service key middleware
- [x] NetworkX graph with 5 seed events (Layer 0-1)
- [x] `GET /api/v1/moments/{path}` returns seed data
- [x] `GET /api/v1/browse/{partial_path}` returns listings
- [x] `GET /api/v1/today` returns today-in-history
- [x] Scene Renderer worker: calls Flash, stores `flash_timepoint_id`
- [x] Graph Expander worker: adds related events around seeds
- [x] `POST /api/v1/index` accepts new moments
- [x] Public/private visibility on all nodes
- [x] Graph serialized to disk, survives restarts

### Phase 2 (Done)
- [x] LLM content judge
- [x] "Today in History" daily cron
- [x] Search endpoint
- [x] Publish endpoint (private → public)
- [x] Graph neighbors endpoint
- [x] Stats endpoint
- [x] Bulk generate (admin)
- [x] Integration tests (full end-to-end workflow)

### Phase 3 (Future)
- [ ] Daedalus (Layer 3) integration
- [ ] Semantic search (beyond keyword matching)
- [ ] Graph visualization API
- [ ] 1000+ Layer 0 nodes
- [ ] 50+ Layer 2 scenes

---

## 12. Gap: Clockchain Proxy in Flash-Deploy

Clockchain's API works but **is not accessible from the public API**. Flash-deploy needs a `clockchain_proxy.py` (similar to `billing_proxy.py`) that forwards:

```
/api/v1/clockchain/*  →  CLOCKCHAIN_SERVICE_URL/api/v1/*
```

This is the **one remaining dependency** before the app can browse the Clockchain.

---

## 13. Services Reference

| Service | Repo | Domain | Status |
|---------|------|--------|--------|
| Landing | timepoint-landing | `timepointai.com` | Live |
| Flash-deploy | timepoint-flash-deploy | `api.timepointai.com` | Live (the gateway) |
| Billing | timepoint-billing | *(internal)* | Live v0.3.0 |
| Clockchain | timepoint-clockchain | *(internal)* | **Live (all phases complete)** |
| App | timepoint-app | `app.timepointai.com` | Planned |

---

**TIMEPOINT · Synthetic Time Travel**

*"Flash renders moments. The Clockchain remembers all of them, connects them, and decides which ones to illuminate next. Flash-deploy opens the door. The App is the window."*
