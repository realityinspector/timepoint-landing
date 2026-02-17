# TIMEPOINT Design Guidelines

**Synthetic Time Travel™**
**v1.0 — February 2026**

Implement these rules on every asset, interface, render, and communication.

---

## 1. Brand Essence

TIMEPOINT renders the unseen past with scholarly steel and cosmic awe.

**Always deliver:**
- Monumental scale + intimate human tension
- Historical precision elevated into the sublime
- Light as architecture, time as physical space
- Reverent weight — never playful, never casual

**Core feeling:** You are standing inside Boullée's Cenotaph, inside Dune's imperial halls, inside a living Cellarius chart — holding the exact moment history happened.

**Litmus test:** Before approving anything, ask: "Does this feel like time itself rendered?" If no, restart.

---

## 2. Core Visual Principles

- **Light as structure** — vertical columns, god rays, slit-scan streaks, internal selenite glow. Every layout must contain at least one dramatic light source that feels architectural.
- **Gold leaf on matte black** — the signature texture pairing.
- **Scale contrast is mandatory** — tiny human figures against impossible cosmic or architectural vastness.
- **Sacred geometry + mechanical precision** — orreries, armillary spheres, causal mandalas.
- **Psychedelic restraint** — never rainbow, always iridescent or spectral when it appears.
- **Materials palette:** patinated bronze, corten weathering (subtle), Vantablack voids, dichroic glass accents, marble veining.

### Reference Board

| Domain | Key References |
|--------|---------------|
| Architecture | Boullée Cenotaph for Newton, Ferriss *Metropolis of Tomorrow*, Tadao Ando light slots, Soane's Museum |
| Film | Dune (Vermette), 2001 Stargate, Blade Runner 2049 (Wallace Corp), Alien (Cobb interiors), Solaris (library), Interstellar (tesseract) |
| Visual Art | Beksiński (cathedral scale, amber/bone), Moebius (clean-line cosmic), Chris Foss (iridescent craft), John Harris (deep-space sublime), Turrell (Roden Crater), Hilma af Klint (sacred geometry), Piranesi (impossible prisons) |
| Design | NASA JPL Visions of the Future, Dieter Rams/Braun, Otl Aicher Munich 1972, Criterion Collection packaging |
| Music/Mood | Vangelis Blade Runner, Brian Eno *Apollo*, Sun Ra *Space Is the Place*, Tool (Alex Grey), Boards of Canada |

---

## 3. Color Palette

### Primary

| Token | Hex | Usage |
|-------|-----|-------|
| **Void Black** | `#050505` | 80% of screen real estate |
| **Patinated Gold** | `#BFA46F` → `#D4AF37` | Accents, light beams, orrery arms |

### Secondary

| Token | Hex | Usage |
|-------|-----|-------|
| **Cosmic Amber** | `#E8C9A0` | Dramatic lighting, highlights |
| **Deep Indigo** | `#0F1C2E` | Secondary depth, panel backgrounds |
| **Marble Grey** | `#A89F91` | Body text, structural panels |
| **Selenite White** | `#F5F0E6` | Subtle internal glows (5% max) |

### CSS Variables (as implemented)

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

### Rules

- Never use pure white or bright primaries
- Gold must always feel metallic and patinated, never flat yellow
- Apply subtle dichroic shift on interactive elements (angle-dependent gold-to-amber)
- Backgrounds: deep voids with 1–2% noise or very slow light-streak animation

---

## 4. Typography

### Display / Hero Headlines

- **Font:** Cinzel (neoclassical high-contrast serif). Fallback: Trajan Pro, Georgia.
- **Treatment:** ALL CAPS, letter-spacing `0.08em`–`0.15em`, extreme tracking on headlines.
- Monumental. Reads as if carved in marble then backlit by an orrery.

### Body / UI

- **Font:** Inter (clean, highly legible sans). Fallback: -apple-system, Segoe UI.
- Weight 300 (light) for body, 500 for emphasis.
- Line height: 1.7–2.0. Ample negative space.

### Monospace / Code / Labels

- **Font:** JetBrains Mono. Fallback: SF Mono, Fira Code.
- Section labels: ALL CAPS, `0.3em`–`0.5em` letter-spacing.
- Terminal blocks: 0.78rem, line-height 1.8.

### Hierarchy (as implemented)

| Level | Font | Size | Weight | Tracking |
|-------|------|------|--------|----------|
| Hero H1 | Cinzel | clamp(2.4rem, 7vw, 4.5rem) | 700 | 0.08em |
| Product Name | Cinzel | 1.4rem | 600 | 0.12em |
| Section Label | JetBrains Mono | 0.6rem | 500 | 0.4em |
| Body | Inter | 0.85–0.92rem | 300 | normal |
| Code/Stats | JetBrains Mono | 0.68–0.78rem | 400 | 0.03em |

---

## 5. Motifs & Iconography

### Signature Motifs (deploy regularly)

- **Armillary spheres / orreries** — hero animation (concentric pulsing rings), loading states, timeline controls
- **Celestial charts** (Cellarius *Harmonia Macrocosmica* style) — subtle backgrounds, data overlays
- **Mandalas as circuit diagrams** — causal provenance graphs, SNAG network visualizations
- **Light columns** — Cathedral of Light technique: vertical 1px gold gradient, center of viewport
- **Voyager Golden Record** diagrammatic icons — scientific annotation style for UI metadata

### As Implemented

- Hero: 3 concentric orrery rings with breathing pulse animation, single lit node on middle ring
- God-ray: radial gradient emanating from center (4% opacity gold)
- Body: fixed vertical light column at 50% viewport width
- Background: SVG fractal noise at 1.5% opacity
- Dividers: light-slit gradients with soft radial bloom
- Scene void headers: horizontal light slit across Vantablack void
- Product cards: top-edge architectural light source

---

## 6. Imagery & Scene Direction

- Photoreal historical accuracy + impossible cinematic lighting (Dune production design + 2001 Stargate)
- Always include human drama at small scale inside vast architecture
- Three-tier fallback: 1. Photoreal, 2. Dramatic painting (Beksiński scale), 3. Celestial diagram
- Never bright, never cartoon, never low-contrast
- Scene images: `saturate(0.7) contrast(1.1) brightness(0.9)` — desaturated, contrasty, slightly dark

**Every generated scene must pass the "Oppenheimer at Trinity" test:** period-perfect + sublime + interrogatable.

---

## 7. UI/UX Principles

- **Dark neoclassical:** recessed void panels, column grids, amber backlighting
- **Negative space is sacred** — section padding: 8rem, generous line-height
- **Interactions:** slow temporal reveals (1s fade-in, staggered delays), breathing orrery animations, light-column dividers
- **Query input** feels like an ancient scroll fused with mission-control terminal
- **Loading states:** orrery gears turning, celestial charts assembling
- **Terminal blocks:** Ron Cobb utilitarian ship interiors — `#040405` background, gold-dim prompts, selenite commands
- **Every screen must feel like you stepped into the Forum Romanum inside a spaceship**

### Developer UX Juxtaposition

The design deliberately places high-art cosmic aesthetics alongside pragmatic developer elements:
- Scene cards (Criterion Collection precision) sit next to terminal quickstart blocks (mission control utility)
- Cinzel monumental headlines contrast with JetBrains Mono `$ git clone` commands
- Product descriptions use reverent prose; stats use terse monospace readouts
- This is not contradiction — it's the Ron Cobb / H.R. Giger contrast from Alien: the utilitarian crew deck and the biomechanical temple are the same ship

---

## 8. Tone of Voice & Writing

- Precise, reverent, quietly grandiose
- Write as if you are the keeper of the Clockchain
- Never hype. Never cute.
- Let the demos speak. No "revolutionary," "groundbreaking," "cutting-edge."
- Technical precision > marketing fluff. Quote real numbers (630+ tests, 14 agents, $0.15–$1.00/run).

**Example:** "Type 'Caesar, 15 March 44 BCE, late morning' and stand on the marble steps with him."

---

## 9. Do's and Don'ts

### Do

- Dramatic volumetric lighting
- Tiny humans in vast temporal space
- Gold leaf + matte black everywhere possible
- Scholarly footnotes in UI when appropriate
- ALL CAPS for headlines, section labels, product names, CTAs

### Never

- Neon, cyberpunk, bright colors
- Cartoon or low-fi styles
- Flat design
- Lowercase hero headlines
- Generic tech gradients
- Pure white backgrounds or text
- Emojis in UI (icons only in prose where semantic: ⚡ ⚖️)

---

## 10. Implementation Notes

### Current Implementation (index.html)

The landing page implements this system as a single self-contained HTML file with inline CSS. No build step, no JS frameworks. The content is the product.

| Element | Implementation |
|---------|---------------|
| Orrery rings | CSS `border-radius: 50%` + `pulse-ring` keyframe animation |
| God-ray | `radial-gradient` centered in hero |
| Light column | `body::after` — fixed 1px vertical gradient |
| Noise texture | Inline SVG `feTurbulence` at 1.5% opacity |
| Light-slit dividers | `linear-gradient` 90deg with radial bloom `::after` |
| Terminal blocks | Semantic `<span>` classes for syntax coloring |
| Scroll reveal | `IntersectionObserver` adding `.visible` class |
| Typography | Google Fonts: Cinzel, Inter, JetBrains Mono |

### File Locations

- `index.html` — Landing page (served by FastAPI at `/`)
- `docs/images/alphago-move37.jpeg` — Hero scene image
- `DESIGN.md` — This document

---

**TIMEPOINT**
Flash · Daedalus · Proteus
Synthetic Time Travel™ is a trademark of TIMEPOINT.
