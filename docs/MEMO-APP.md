# HANDOFF MEMO: timepoint-app Agent
**From:** timepoint-landing · Feb 2026
**Re:** Build the TIMEPOINT app — browse the Clockchain, render scenes, at app.timepointai.com

---

## 1. What You Are Building

**timepoint-app** is the **user-facing frontend** for TIMEPOINT's platform. It lives at `app.timepointai.com` and gives users a way to:

1. **Browse the Clockchain** — explore an ever-growing graph of historical moments organized by temporal URLs
2. **View scenes** — read Flash-generated narratives with images, characters, and dialog
3. **Request new scenes** — type a moment, spend credits, get a rendered scene
4. **Interact with characters** — chat with historical figures, run surveys, extend dialog
5. **Navigate time** — jump forward/backward from any scene
6. **Manage their account** — sign in, buy credits, publish private scenes, view history

The app is a **frontend SPA** that calls one backend:
- **timepoint-billing** (`api.timepointai.com`) — auth, credits, generation, payments, browse/search

The app does NOT call Flash or Clockchain directly. All requests go through billing, which has a built `flash_client.py` and routes browse/search to Clockchain internally.

**Key integration reality**: Flash's billing integration is **fully deployed** — three auth paths, user resolution by external_id, callback URLs, transaction type tagging. Billing already has its Flash client built.

---

## 2. Full Service Map

```
timepointai.com          → timepoint-landing     (static marketing)
app.timepointai.com      → timepoint-app         ← YOU ARE BUILDING THIS
api.timepointai.com      → timepoint-billing     (Auth0, Stripe, API keys, relay)
(internal)               → timepoint-flash       (credit ledger + generation)
(internal)               → timepoint-clockchain  (graph index + workers)
```

### What the App Calls

```
app.timepointai.com
        │
        ├──► api.timepointai.com (billing)
        │       Auth0 JWT in every request
        │       ├── POST /api/v1/generate/stream    → render a scene
        │       ├── GET  /api/v1/credits/balance     → show credits
        │       ├── GET  /api/v1/credits/costs       → show pricing
        │       ├── POST /api/v1/billing/checkout    → buy credits (Stripe)
        │       ├── GET  /api/v1/timepoints/{id}     → fetch full scene
        │       ├── POST /api/v1/auth/login          → session start
        │       └── GET  /api/v1/auth/me             → user profile
        │
        └──► api.timepointai.com (billing proxies to clockchain)
                ├── GET  /api/v1/moments/{path}      → moment metadata
                ├── GET  /api/v1/browse/{path}        → browse listings
                ├── GET  /api/v1/today                → today in history
                ├── GET  /api/v1/search?q=...         → search
                ├── GET  /api/v1/graph/neighbors/{id} → related events
                └── GET  /api/v1/random               → random moment
```

All requests go to `api.timepointai.com`. Billing routes browse/search requests to Clockchain internally. The app doesn't need to know about Clockchain's internal URL.

---

## 3. Design System

The app MUST follow the TIMEPOINT design system defined in `timepoint-landing/DESIGN.md`. This is not optional — visual consistency across landing and app is critical.

### Core Rules

- **Dark neoclassical** — `#050505` void black dominates, gold accents
- **Cinzel** for headlines (ALL CAPS, wide tracking), **Inter** for body, **JetBrains Mono** for code/labels
- **Gold leaf on matte black** — the signature texture
- **Never**: neon, bright colors, flat design, lowercase hero text, emojis in UI, pure white
- **Always**: dramatic volumetric lighting, negative space, reverent weight

### CSS Variables (match landing page exactly)

```css
:root {
    --void:         #050505;
    --void-near:    #080808;
    --void-mid:     #0b0b0e;
    --void-far:     #0f1020;
    --indigo:       #0F1C2E;
    --gold:         #BFA46F;
    --gold-bright:  #D4AF37;
    --gold-dim:     #8a7033;
    --amber:        #E8C9A0;
    --marble:       #A89F91;
    --selenite:     #F5F0E6;
}
```

### Typography

| Level | Font | Weight | Tracking |
|-------|------|--------|----------|
| Page titles | Cinzel | 700 | 0.08em |
| Card titles | Cinzel | 600 | 0.12em |
| Section labels | JetBrains Mono | 500 | 0.4em |
| Body text | Inter | 300 | normal |
| Stats/metadata | JetBrains Mono | 400 | 0.03em |

### Key Design Elements from Landing

- **Orrery rings** — use as loading/generating animation
- **Light column** — fixed vertical gold gradient, center of viewport
- **Noise texture** — SVG feTurbulence at 1.5% opacity on backgrounds
- **Light-slit dividers** — gold gradient with radial bloom between sections
- **Scene cards** — top-edge architectural light source, Criterion Collection precision

### The Developer/Scholar Juxtaposition

The app should feel like the landing page come alive — monumental Cinzel headings for moment titles, JetBrains Mono for metadata readouts (coordinates, dates, figures), Inter for narrative body text. Like browsing the Forum Romanum inside a spaceship.

---

## 4. Pages & Views

### 4.1 Home (`/`)

- **Hero**: Animated orrery (from landing), search bar front and center
- **Today in History**: 3-5 cards from `GET /api/v1/today` — auto-generated daily content
- **Recently Published**: Latest public timepoints
- **Browse by Era**: Links to `/browse/` paths (Ancient, Medieval, Early Modern, Modern, Contemporary)
- **Stats bar**: Total moments indexed, scenes rendered, graph edges (from `/api/v1/stats`)

### 4.2 Browse (`/browse/{path}`)

- Hierarchical temporal browsing
- `/browse/1969` → grid of months with event counts
- `/browse/1969/july` → grid of days
- `/browse/1969/july/20` → list of events with metadata cards
- Each card shows: event name, one-liner, tags, figures, layer depth indicator
- Layer 2+ cards show scene preview thumbnail
- Layer 0-1 cards show "Generate this moment" CTA (requires login + credits)

### 4.3 Moment Detail (`/moment/{full_path}`)

- **If Layer 2+**: Full scene display
  - Hero image (if generated)
  - Narrative text (2-3 paragraphs)
  - Character cards with portraits/bios
  - Dialog excerpts
  - Metadata sidebar: date, location, era, figures, sources, SNAG scores
  - "Talk to Characters" button → chat interface
  - "Jump Forward/Backward" → temporal navigation
  - Related moments (from graph neighbors)
- **If Layer 0-1**: Metadata display with "Render This Moment" CTA
- **If private**: Only visible to owner, "Publish" button to make public

### 4.4 Search (`/search?q=...`)

- Full-text search across moment names, descriptions, figures, tags
- Results as cards with metadata preview
- Filter by era, location, tags
- Sort by relevance, date, recently added

### 4.5 Generate (`/generate`)

- Large text input: "Describe a moment in history..."
- Preset selector: balanced (default), hd (costs more credits), hyper (fast)
- Credit cost shown before generating
- Generates via `POST /api/v1/generate/stream` (SSE)
- Real-time progress: "Judging query... Grounding... Generating scene... Rendering image..."
- Result appears inline, user can publish or keep private

### 4.6 Character Chat (`/moment/{path}/chat/{character_id}`)

- Chat interface with a historical figure from a rendered scene
- Character portrait + bio in sidebar
- Message input, streaming responses
- Session history

### 4.7 Account (`/account`)

- Profile (Auth0 user info)
- Credit balance + transaction history
- "Buy Credits" → Stripe Checkout
- My Timepoints (private + published)
- API Keys (for developers) → link to api.timepointai.com docs

### 4.8 Auth

- Login: Auth0 Universal Login (redirect)
- Callback: `/auth/callback` — handle Auth0 redirect, store JWT
- Logout: Clear session, revoke token

---

## 5. Auth Flow

### Login

1. User clicks "Sign In"
2. Redirect to Auth0 Universal Login (`https://{AUTH0_DOMAIN}/authorize`)
3. User authenticates (email, Google, Apple, GitHub)
4. Auth0 redirects to `app.timepointai.com/auth/callback` with authorization code
5. App exchanges code for JWT (via Auth0 SDK — `getAccessTokenSilently()`)
6. App sends JWT to `POST /api/v1/auth/login` on billing
7. Billing validates JWT, calls Flash `POST /users/resolve` with `external_id: {auth0_sub}` → auto-creates user + credit account (50 signup credits) if first login
8. Store JWT in memory (not localStorage — XSS risk) or httpOnly cookie
9. Include JWT in all requests to `api.timepointai.com`

### Token Refresh

- Auth0 JWT expiry: 15 minutes (configurable)
- Use Auth0 SDK `getAccessTokenSilently()` — handles refresh automatically via rotating refresh tokens
- Falls back to re-login if refresh fails

### Unauthenticated Access

- Browse and search work without login (public Layer 0-1 data)
- Viewing full scenes (Layer 2) requires free login
- Generating scenes requires login + credits
- Buying credits requires login + Stripe

---

## 6. Tech Stack

### Recommended

- **Framework**: Next.js (App Router) or Vite + React
  - Next.js if you want SSR for SEO on public moments
  - Vite + React if pure SPA is fine (simpler, billing handles all API calls)
- **Styling**: Tailwind CSS + CSS variables from design system
- **Auth**: Auth0 React SDK (`@auth0/auth0-react`)
- **State**: React Query / TanStack Query (for API data caching)
- **Streaming**: native EventSource API for SSE from `/generate/stream`
- **Deployment**: Railway (Docker) or Vercel/Netlify (static)

### Auth0 SDK Setup

```typescript
import { Auth0Provider } from '@auth0/auth0-react';

<Auth0Provider
  domain={process.env.NEXT_PUBLIC_AUTH0_DOMAIN}
  clientId={process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID}
  authorizationParams={{
    redirect_uri: window.location.origin + '/auth/callback',
    audience: 'https://api.timepointai.com',
    scope: 'openid profile email',
  }}
>
  <App />
</Auth0Provider>
```

### API Client

```typescript
const API_BASE = 'https://api.timepointai.com/api/v1';

async function apiCall(path: string, options?: RequestInit) {
  const token = await getAccessTokenSilently();
  return fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
}

// Browse (no auth needed for public data)
const today = await fetch(`${API_BASE}/today`).then(r => r.json());

// Generate (auth + credits required)
const response = await apiCall('/generate/stream', {
  method: 'POST',
  body: JSON.stringify({ query: 'Ides of March, 44 BCE', preset: 'balanced' }),
});
// Handle SSE stream from response
```

---

## 7. SSE Streaming for Generation

Flash supports streaming generation via SSE. Billing proxies this through:

```typescript
async function generateScene(query: string, preset: string) {
  const token = await getAccessTokenSilently();
  const response = await fetch(`${API_BASE}/generate/stream`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query, preset }),
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    // Parse SSE events: status updates, partial results, final scene
    // Update UI progressively
  }
}
```

Show progress stages in the UI:
- "Evaluating query..." (judge)
- "Researching historical context..." (grounding)
- "Building the scene..." (generation)
- "Rendering image..." (image generation)
- "Complete" → display full scene

---

## 8. Deployment

### Railway (Docker)

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
```

Or if using Next.js with SSR:
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### Railway Config

```json
{
  "$schema": "https://railway.com/railway.schema.json",
  "build": { "builder": "DOCKERFILE", "dockerfilePath": "Dockerfile" },
  "deploy": {
    "healthcheckPath": "/",
    "healthcheckTimeout": 30,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

### Env Vars

```bash
NEXT_PUBLIC_AUTH0_DOMAIN=your-tenant.auth0.com
NEXT_PUBLIC_AUTH0_CLIENT_ID=...
NEXT_PUBLIC_API_BASE=https://api.timepointai.com
```

---

## 9. Key UX Flows

### First Visit (no login)

1. Land on home → see Today in History cards, search bar, stats
2. Browse moments by era/year/month
3. Click a public Layer 2 moment → see metadata preview, "Sign in to view full scene"
4. Search for events → see results with metadata
5. Click "Sign In" → Auth0 → redirected back → billing calls Flash `/users/resolve` → account auto-created with 50 free credits

### Returning User (logged in)

1. Home shows personalized: "Your Timepoints", credit balance, Today in History
2. Browse/search with full Layer 2 access on public scenes
3. Click "Generate" → enter query → see credit cost → confirm → watch SSE progress → scene appears
4. Click "Publish" on a private scene → it becomes public, enriching the Clockchain
5. Click character → chat interface opens
6. Click "Jump Forward 1 Year" → temporal navigation generates next scene

### Credit Purchase

1. User runs out of credits mid-generation → "Insufficient credits" modal
2. "Buy Credits" → pricing cards (50 credits / $4.99, 200 / $14.99, etc.)
3. Click → Stripe Checkout opens → payment → webhook → credits appear instantly
4. Continue generating

---

## 10. Key Design Decisions

1. **SPA, not MPA** — single page app for smooth navigation
2. **All API calls through billing** — app never calls Flash or Clockchain directly
3. **Auth0 React SDK** — handles login, token refresh, session management
4. **TIMEPOINT design system** — must match landing page aesthetics exactly
5. **SSE for generation** — real-time progress, not polling
6. **Public browse without login** — Layer 0-1 is free, login for Layer 2
7. **Credits shown prominently** — always visible in header, cost shown before every action
8. **Railway** for deployment
9. **Mobile-responsive** — works on phones, but desktop is the primary experience

---

## 11. What Success Looks Like

### Phase 1 (Build Now)
- [ ] Auth0 login/logout working
- [ ] Home page with Today in History (from Clockchain via billing)
- [ ] Browse view (hierarchical temporal navigation)
- [ ] Moment detail view (full scene display for Layer 2)
- [ ] Search
- [ ] Credit balance display
- [ ] Design system implemented (dark, gold, Cinzel/Inter/JetBrains)
- [ ] Deployed on Railway at app.timepointai.com

### Phase 2 (Generation)
- [ ] Generate view with SSE streaming
- [ ] Preset selector with credit cost display
- [ ] Private/public toggle + publish flow
- [ ] Stripe credit purchase
- [ ] Character chat interface
- [ ] Temporal navigation (jump forward/backward)

### Phase 3 (Polish)
- [ ] Graph visualization (neighbors/connections view)
- [ ] User profile + timepoint history
- [ ] API key management (link to developer docs)
- [ ] Mobile optimization
- [ ] Loading animations (orrery rings)

---

## 12. Services Reference

| Service | Repo | Domain | Status |
|---------|------|--------|--------|
| Landing | timepoint-landing | `timepointai.com` | Live |
| Flash | timepoint-flash-deploy | *(internal)* | Live (billing integration deployed) |
| Clockchain | timepoint-clockchain | *(internal)* | Building |
| App | timepoint-app | `app.timepointai.com` | **BUILD THIS** |
| Billing | timepoint-billing | `api.timepointai.com` | Building (flash_client.py done) |

---

**TIMEPOINT · Synthetic Time Travel™**

*"The App is the window into the Clockchain. Every moment in history, browsable, searchable, renderable — standing inside time itself."*
