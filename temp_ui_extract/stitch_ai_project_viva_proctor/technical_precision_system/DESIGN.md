---
name: Technical Precision System
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#424656'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#737687'
  outline-variant: '#c2c6d9'
  surface-tint: '#0053da'
  primary: '#004cca'
  on-primary: '#ffffff'
  primary-container: '#0062ff'
  on-primary-container: '#f3f3ff'
  inverse-primary: '#b4c5ff'
  secondary: '#565e74'
  on-secondary: '#ffffff'
  secondary-container: '#dae2fd'
  on-secondary-container: '#5c647a'
  tertiary: '#48586d'
  on-tertiary: '#ffffff'
  tertiary-container: '#607087'
  on-tertiary-container: '#eef3ff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dbe1ff'
  primary-fixed-dim: '#b4c5ff'
  on-primary-fixed: '#00174b'
  on-primary-fixed-variant: '#003ea8'
  secondary-fixed: '#dae2fd'
  secondary-fixed-dim: '#bec6e0'
  on-secondary-fixed: '#131b2e'
  on-secondary-fixed-variant: '#3f465c'
  tertiary-fixed: '#d3e4fe'
  tertiary-fixed-dim: '#b7c8e1'
  on-tertiary-fixed: '#0b1c30'
  on-tertiary-fixed-variant: '#38485d'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  display:
    fontFamily: Syne
    fontSize: 4.5rem
    fontWeight: '800'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Syne
    fontSize: 3.5rem
    fontWeight: '800'
    lineHeight: '1.2'
    letterSpacing: -0.015em
  headline-lg-mobile:
    fontFamily: Syne
    fontSize: 2.5rem
    fontWeight: '800'
    lineHeight: '1.2'
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Syne
    fontSize: 2rem
    fontWeight: '700'
    lineHeight: '1.3'
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Syne
    fontSize: 1.5rem
    fontWeight: '700'
    lineHeight: '1.4'
    letterSpacing: 0em
  body-lg:
    fontFamily: Inter
    fontSize: 1.125rem
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: 0em
  body-md:
    fontFamily: Inter
    fontSize: 1rem
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: 0em
  body-sm:
    fontFamily: Inter
    fontSize: 0.875rem
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: 0em
  label-lg:
    fontFamily: Inter
    fontSize: 0.875rem
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.05em
  label-md:
    fontFamily: Inter
    fontSize: 0.75rem
    fontWeight: '500'
    lineHeight: '1'
    letterSpacing: 0em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 12px
  md: 24px
  lg: 40px
  xl: 64px
  container-max: 1280px
  gutter: 24px
---

## Brand & Style

The design system is engineered for a high-performance AI evaluation environment. It balances technical authority with a progressive, tech-forward aesthetic. The brand personality is clinical yet visionary—prioritizing the clarity of complex data while maintaining a bold visual identity that reflects the cutting-edge nature of machine learning.

The style is **Modern Corporate with High-Contrast Typography**. It utilizes expansive white space, a disciplined primary color application, and a drastic typographic hierarchy to guide users through dense analytical workflows. The aesthetic avoids unnecessary decoration, relying instead on structural geometry and purposeful depth to convey reliability and sophistication.

## Colors

The palette is anchored by a vibrant, high-energy primary blue (#0062ff), signifying intelligence and action. This is paired with a deep "slate" secondary color for text and structural elements to establish a sense of gravity and professional weight.

- **Primary:** Reserved for primary actions, active states, and brand-critical indicators.
- **Secondary:** Used for deep contrast in headings and high-level navigation.
- **Neutral:** A range of cool grays provides the foundation for data tables, card backgrounds, and subtle borders, ensuring the interface feels airy and organized.
- **Success/Warning/Error:** Standardized semantic colors should be used with high saturation to stand out against the neutral backdrop.

## Typography

This design system introduces a drastic contrast between expressive display type and functional body text. 

**Syne** is utilized for all headlines. Its geometric, wide-set proportions and heavy weights (700-800) create an impactful, authoritative presence. For maximum impact, use `display` and `headline-lg` roles for landing moments and major dashboard sections.

**Inter** is the workhorse for all functional content. It provides exceptional legibility for data-heavy views. By maintaining a standard `400` weight for body text against the `800` weight of headlines, the system achieves a clear, professional hierarchy.

**Guidelines:**
- All headlines must use a "tight" line height to maintain the blocky, architectural feel of the font.
- Labels and Small UI text should use increased letter spacing when uppercase to improve scanability.

## Layout & Spacing

The layout follows a **Fluid Grid** model with a 12-column structure for desktop. The system is built on an 8px base unit, ensuring consistent rhythm across all components.

- **Desktop (1280px+):** 12 columns, 24px gutters, 40px side margins.
- **Tablet (768px - 1279px):** 8 columns, 16px gutters, 24px side margins.
- **Mobile (< 767px):** 4 columns, 16px gutters, 16px side margins.

Horizontal spacing should favor generous "breathing room" around high-impact typography to emphasize the editorial feel of the design.

## Elevation & Depth

To maintain a professional and technical feel, the design system avoids heavy, traditional shadows. Instead, it utilizes **Tonal Layers and Low-Contrast Outlines**.

- **Surface Levels:** The background is a very light neutral (#f8fafc). Secondary surfaces (cards, sidebars) use pure white (#ffffff) to appear "raised."
- **Borders:** Use 1px solid borders in a soft gray (#e2e8f0) to define containers. 
- **Active Elevation:** Only use shadows for interactive elements in an "active" or "floating" state (e.g., modals or dropdowns). These shadows should be extremely diffused: `0px 10px 25px rgba(0, 0, 0, 0.04)`.

## Shapes

The design system uses a **Rounded** shape language to soften the aggressive nature of the high-impact typography. 

- **Standard Components:** Buttons, input fields, and small cards use a 0.5rem (8px) corner radius.
- **Large Containers:** Dashboard widgets and main content sections use a 1rem (16px) radius to create a distinct framing effect.
- **Interactive Elements:** Checkboxes and toggle tracks follow the 0.25rem (4px) or fully rounded pill-shape rule depending on the context.

## Components

### Buttons
Primary buttons use the #0062ff background with white text. To maintain the "drastic" typographic style, button labels should use **Inter Bold** with a slightly tighter letter spacing. The height is standardized at 48px for primary actions to ensure a "chunky," authoritative feel.

### Cards
Cards are the primary container for AI evaluation data. They should feature a white background, a 1px soft border, and no shadow. The headline inside a card should use `headline-sm` (Syne) to ensure the technical data underneath feels subordinate and organized.

### Input Fields
Inputs use a subtle gray background (#f1f5f9) that shifts to white with a 2px blue border on focus. This high-contrast focus state is critical for the "Precision" aspect of the brand.

### Chips & Badges
Use high-contrast fills for status chips. For example, a "Success" chip should use a pale green background with deep emerald text, utilizing a pill-shaped (rounded-full) geometry to contrast against the more rectangular cards.

### Lists & Data Tables
Tables are the core of the evaluation experience. Use `body-sm` (Inter) for data rows to maximize density, while table headers should use `label-lg` (Inter) in all caps to provide a clear anchor point for the eye.