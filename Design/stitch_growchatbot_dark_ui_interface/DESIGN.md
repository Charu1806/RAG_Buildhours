---
name: Luminous Institutional
colors:
  surface: '#051424'
  surface-dim: '#051424'
  surface-bright: '#2c3a4c'
  surface-container-lowest: '#010f1f'
  surface-container-low: '#0d1c2d'
  surface-container: '#122131'
  surface-container-high: '#1c2b3c'
  surface-container-highest: '#273647'
  on-surface: '#d4e4fa'
  on-surface-variant: '#c9c4d8'
  inverse-surface: '#d4e4fa'
  inverse-on-surface: '#233143'
  outline: '#938ea1'
  outline-variant: '#484555'
  surface-tint: '#cabeff'
  primary: '#cabeff'
  on-primary: '#32009a'
  primary-container: '#947dff'
  on-primary-container: '#2b0088'
  inverse-primary: '#613de0'
  secondary: '#41eec2'
  on-secondary: '#00382b'
  secondary-container: '#00d1a7'
  on-secondary-container: '#005441'
  tertiary: '#ffb95f'
  on-tertiary: '#472a00'
  tertiary-container: '#ca8100'
  on-tertiary-container: '#3e2400'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e6deff'
  primary-fixed-dim: '#cabeff'
  on-primary-fixed: '#1c0062'
  on-primary-fixed-variant: '#4918c8'
  secondary-fixed: '#55fcd0'
  secondary-fixed-dim: '#28dfb5'
  on-secondary-fixed: '#002118'
  on-secondary-fixed-variant: '#00513f'
  tertiary-fixed: '#ffddb8'
  tertiary-fixed-dim: '#ffb95f'
  on-tertiary-fixed: '#2a1700'
  on-tertiary-fixed-variant: '#653e00'
  background: '#051424'
  on-background: '#d4e4fa'
  surface-variant: '#273647'
typography:
  display-lg:
    fontFamily: DM Sans
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: DM Sans
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: DM Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm-mobile:
    fontFamily: DM Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  mono-data:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  container-margin: 24px
  gutter: 16px
  chat-gap: 12px
  section-padding: 32px
---

## Brand & Style

The design system is engineered for a high-trust, data-centric financial environment. It employs a **Modern Corporate** aesthetic with **Glassmorphic** influences to alleviate the visual weight of a deep dark theme. 

The target audience consists of investors seeking clarity and precision. The UI must evoke a sense of "Institutional Intelligence"—stable, sophisticated, and fast. By utilizing deep navy foundations contrasted with vibrant neon accents, the interface feels like a premium financial terminal reimagined for a conversational era. High whitespace within cards and crisp borders prevent the dark palette from feeling claustrophobic.

## Colors

This design system utilizes a layered dark-mode strategy. The primary background provides depth, while the surface color creates a "raised" container effect for chat bubbles and data modules.

- **Primary (#7C5CFC):** Used for key actions, focus states, and the user's chat presence.
- **Secondary (#00D4AA):** Indicates growth, success, "Verified" statuses, and positive financial trends.
- **Warning (#F59E0B):** Reserved strictly for legal disclaimers, risk disclosures, and volatility alerts.
- **Neutral/Muted (#94A3B8):** Applied to metadata, timestamps, and secondary labels to maintain hierarchy.

## Typography

The typography system pairs **DM Sans** for headings to provide a modern, geometric feel, with **Inter** for all functional and body text to ensure maximum legibility at small sizes.

For mutual fund tickers or specific numerical data, a monospaced font (JetBrains Mono) is introduced to ensure alignment in tabular data. Headings use tighter letter spacing to maintain a "locked-in" professional look, while body text uses standard tracking to facilitate long-form reading of financial explanations.

## Layout & Spacing

The design system follows a **Fixed Grid** model for desktop (centered 800px chat container) and a **Fluid** model for mobile. 

The rhythm is based on a 4px baseline. Chat bubbles are separated by a 12px vertical gap to signify grouped conversation flow, while distinct "Insight Cards" (like fund performance summaries) use a 24px margin to stand out from the stream. On mobile, horizontal padding reduces to 16px to maximize the real estate for complex financial tables or charts.

## Elevation & Depth

Depth is communicated through **Tonal Layering** and **Subtle Glows**. 

1.  **Level 0 (Background):** #0F1117 - The infinite base.
2.  **Level 1 (Cards/Input):** #1A1D2E - Used for the main chat interface and input field.
3.  **Level 2 (Active Elements):** #25293D - Used for hover states or active card selections.

**Shadows:** Use a single, highly diffused shadow for cards: `0px 10px 30px rgba(0, 0, 0, 0.5)`. 
**Accents:** Primary buttons and active chat bubbles feature a subtle 15% opacity outer glow of their own hex color to simulate a light-emitting source in the dark environment.

## Shapes

The shape language is defined by **Medium Roundedness**. 

- **Standard Elements:** Buttons, Input fields, and Chat bubbles use a 12px (`rounded-md`) radius.
- **Containers:** Large data cards and the main chat viewport use a 16px (`rounded-lg`) radius.
- **Interactive Chips:** Suggested questions use a 24px (`rounded-xl`) or full pill-shape to distinguish them from message bubbles.

Avoid sharp 0px corners to maintain an approachable, modern fintech vibe.

## Components

- **Chat Bubbles:** Assistant bubbles use the Surface color (#1A1D2E) with a subtle 1px border (#2D314D). User bubbles use the Primary color (#7C5CFC).
- **Primary Button:** Solid #7C5CFC background with #F1F5F9 text. High-contrast and elevated.
- **Suggested Chips:** Outlined buttons with a #2D314D border. Upon hover, the border transitions to Primary Purple.
- **Input Field:** Anchored to the bottom. Uses the Surface color with a persistent 1px border. The placeholder text uses the Muted color (#94A3B8).
- **Data Cards:** For fund performance, use a 1px top-border gradient from Secondary (#00D4AA) to transparent to signify "Growth" cards.
- **Disclaimers:** Contained in a low-opacity Amber (#F59E0B) tint box with a left-edge 4px accent bar.
- **Scrollbars:** Minimalist, using #2D314D for the track and #94A3B8 for the thumb, with a 4px width.