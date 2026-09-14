# Design — ImmuAtlas

A locked design system for this app. Every page reads this before it changes
how it looks. The system is deliberately hand-written vanilla CSS (no framework)
and works fully offline and with no JavaScript — both are project constraints,
not accidents.

## Genre
modern-minimal, editorial-leaning. A public-health data product: the job is to
make honest WHO immunisation figures readable, never to sell. Confident
typography and generous space carry the "wow"; there is no decorative chrome.

## Macrostructure family
- **Landing (1A):** Marquee-hero → stat grid → interactive vaccine cards → data
  band → face-off band → CTA grid. (`vaxvision-landing.css`, `lp-`/`explore-`/
  `snapshot-`/`vc-` classes.)
- **Data pages (2A, 3A, infections, above-average):** filter-bar → outcome
  headline (verdict banner / KPI row) → result table(s) → method note.
- **Content page (1B mission):** section-head rhythm → persona master/detail →
  team grid.

All pages share the header, hero band, and footer from `base.html`.

## Theme — water-blue (hex, to match the shipped code)
| Token | Value | Role |
|---|---|---|
| `--bg` | `#f4f9fd` | paper (a hair off white toward the blue anchor) |
| `--bg-sunk` | `#e4f0fa` | sunk panels, table heads |
| `--bg-deep` | `#082f49` | deep-ocean footer / tooltips |
| `--ink` | `#0c2a42` | body text (~12:1 on paper) |
| `--ink-muted` | `#4a5a68` | secondary text |
| `--accent` | `#0369a1` | azure — primary accent (~5.9:1) |
| `--accent-lift` | `#06b6d4` | cyan — the signature "water" accent |
| `--accent-strong` | `#075985` | button hover |
| `--accent-wash` | `#e0f2fe` | faint sky fill |
| `--outcome` | `#c2410c` | coral — disease/outcome figures |
| `--rule` | `#d3e2ee` | hairlines |
| `--focus` | `#0369a1` | focus ring |

Contrast targets WCAG AA (4.5:1 body). Colour never carries meaning alone — every
status is also spelled out in words.

## Typography
- **Display:** Fraunces, weight 600, roman (never italic headers).
- **Body:** Public Sans, weight 400.
- **Scale (real hierarchy):** body 1rem/1.65 · `h3` ≈ 1.12rem · `h2` / section
  heads `--text-2xl` clamp(1.5→2rem) · hero title clamp(2→2.75rem) · landing hero
  clamp(2→3.1rem). Display headings track `-.02em`.

## Spacing
4-point named scale (`--space-1 … --space-6`). Pages use named tokens, not raw values.

## Elevation & radius
- **Radius:** `--radius` 3px is the squared base (keeps the accent-top-edge figure
  cards flush); `--radius-sm/md/lg` = 8/12/16px for soft cards, tables, banners.
- **Shadow:** one ocean-tinted scale — `--shadow-sm` / `--shadow-md` / `--shadow-lg`.
  Raised surfaces reference these, not ad-hoc rgba values.

## The signature motif
A short cyan (`--accent-lift`) segment sits on the hairline rule above every
section heading, and a hairline azure→cyan gradient runs along the top of the
hero band. This single repeated water mark is what ties the pages together.

## Motion
- One easing: `--ease-out` cubic-bezier(.2,.6,.2,1). Never the browser default.
- Transitions animate `transform`/`opacity`/`background` only.
- `prefers-reduced-motion: reduce` collapses all motion. Every interaction works
  with no JavaScript (CSS radios, `<details>`, `:focus-within`, `@media (hover)`).

## CTA voice
- Primary: filled `--accent`, `--radius`, hover → `--accent-strong`.
- Secondary/ghost: `--accent` outline on transparent, hover → `--accent-wash`.

## What pages MUST share
Wordmark, the two fonts, the water accent + its placement (the section mark and
hero top-rule), the CTA voice, the section-head rhythm, the honest-denominator
copy discipline (every rate names what it was calculated against).

## What pages MAY differ on
Macrostructure within the family above, and the landing page's richer enrichment
(hand-built SVG). Data pages stay function-first — no decorative imagery.
