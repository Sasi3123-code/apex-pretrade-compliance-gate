# Design System: Apex Pre-Trade Compliance Gate (`ConardLi/garden-skills`)

Built according to **[`ConardLi/garden-skills` (`web-design-engineer`)](https://github.com/ConardLi/garden-skills)** (`SKILL.md`, `references/design-calibration.md`, `references/failure-patterns.md`, and `references/style-recipes/linear.md` + `bloomberg-terminal.md` + `tufte-dataink.md`).

---

## 1. Design Read & Five Dials Calibration (`references/design-calibration.md`)

```yaml
Design Read:
  artifact: Operational Pre-Trade Compliance Gate & Financial Impact Dashboard
  audience: Portfolio Managers, Trading Desk, Chief Compliance Officers (SEC Rule 206(4)-7)
  visual-language: Modern Builder Tool / Institutional Data-First (Linear warm dark + Bloomberg tabular precision)
  mode: redesign-overhaul (progressive disclosure via collapsible dropdowns)
  visual-variance: 3      # Stable grid spine, predictable scanning, zero decorative clutter
  motion-intensity: 2     # Crisp 150ms ease-out state transitions; respects prefers-reduced-motion
  information-density: 8  # High analytical value, gated behind progressive-disclosure dropdowns
  asset-dependence: 2     # Typography, tabular numerals, and hairline structure carry the artifact
  brand-fidelity: 8       # Strict adherence to recipe tokens; zero rogue hues
```

---

## 2. Four Positioning Questions (`SKILL.md` Step 3a)

- **Narrative role**: Instant go/no-go decision gate first (Verdict + Payment Saved), followed by on-demand progressive-disclosure dropdowns for audit evidence.
- **Viewing distance**: `1m` desktop/laptop workstation (`14px` body, `12px–13px` tabular mono data, compact padding).
- **Visual temperature**: Quiet authority, restrained confidence, zero marketing theatrics.
- **Capacity check**: Above-the-fold contains only the unified 4-stat summary bar, the trade selector, and the primary verdict card. All secondary tables and breakdowns live inside collapsible dropdowns (`st.expander`).

---

## 3. Contextual Failure Patterns Repaired (`references/failure-patterns.md`)

1. **No Rounded Card + Colored Left-Border Accent (`SKILL.md` Anti-Cliché #2)**:
   - *Removed*: `border-left: 4px solid` banners.
   - *Replaced with*: `1px solid rgba(255,255,255,0.06)` hairline borders (`linear.md`) and subtle semantic status pills.
2. **No Cardification (`failure-patterns.md` → Layout and Components)**:
   - *Removed*: Separate floating metric boxes for every number.
   - *Replaced with*: A single unified summary bar divided by `1px` vertical hairlines, and collapsible dropdown panels (`st.expander`) for secondary sections.
3. **No Repeated Section Header Formula (`failure-patterns.md` → Marketing & Multi-section)**:
   - *Removed*: Mechanical uppercase `.eyebrow` labels above every heading.
   - *Replaced with*: Direct `Inter Tight` headings and concise inline metadata badges.
4. **No Shape Drift (`failure-patterns.md` → Layout and Components)**:
   - Strict radius grammar: `6px` (chips/badges/buttons), `12px` (dropdown containers/tables), `16px` (primary verdict surface). Never above `16px`.
5. **No Emoji (`SKILL.md` Emoji Rules)**:
   - Zero emojis across the entire application.

---

## 4. Style Recipes & Tweaks (`references/style-recipes/`)

Exposed live in the **Tweaks** dropdown so the user can switch recipes or expand/collapse all dropdowns in real time:

1. **`Linear Warm Dark` (`references/style-recipes/linear.md` — Default)**
   - Ground: `#08090A` · Surface 1: `#16171C` · Surface 2: `#1E1F25` · Hairline: `rgba(255,255,255,0.06)`
   - Primary Text: `#F7F8F8` · Secondary: `#9CA3AF` · Muted: `#6B7280` · Accent: `#5E6AD2`
   - Fonts: `Inter Tight` (600, `-0.02em`) + `Inter` (400/500) + `JetBrains Mono` (`tabular-nums`)
2. **`Bloomberg Terminal` (`references/style-recipes/bloomberg-terminal.md`)**
   - Ground: `#0A0E1A` · Surface 1: `#11172A` · Surface 2: `#1A2138` · Hairline: `#2A3050`
   - Amber Primary: `#FFA02F` · Pass: `#00B96B` · Breach: `#F23645` · Radius: `2px` · Font: `JetBrains Mono`
3. **`Tufte Data-Ink Paper` (`references/style-recipes/tufte-dataink.md`)**
   - Ground: `#FBFAF6` (Warm Paper) · Surface 1: `#F3EFE6` · Ink: `#1B1B1A` · Rules: `#D8D2C2`
   - Data Colors: Warm Red `#A6300E` & Cool Slate `#3E4A5C` · Radius: `0px`
