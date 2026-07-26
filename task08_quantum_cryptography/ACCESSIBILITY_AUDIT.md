# Task 8 accessibility audit

## Scope and target

- **Surface:** the single-page Task 8 browser calculator in `task08_quantum_cryptography/app/`.
- **Target:** WCAG 2.2 Level AA for desktop and responsive browser use.
- **Primary journey:** set θ and φ, compare the two probabilities, inspect the live graph, run the finite-photon extension, advance its seed, use a preset and reset the official example.
- **Test engine:** headless Chromium with the browser accessibility tree enabled.
- **Viewports:** 1440 × 1100, 800 × 900 with 200% text, and 320 × 800.

This is a project-level engineering audit, not a third-party accessibility certification. It combines automated assertions, browser accessibility-tree inspection, keyboard testing and visual review. Testing with users of VoiceOver, NVDA or other assistive technologies remains valuable before public deployment.

## Result

The Stage 6 audit passed all eleven evidence groups with **zero detected WCAG 2.2 AA violations in the tested scope**.

```text
Task 8 accessibility audit: PASS
(11 evidence groups, 0 detected WCAG 2.2 AA violations)
```

Run the repeatable audit from the repository root with:

```bash
NODE_PATH=/path/to/node_modules \
TASK08_CHROMIUM_EXECUTABLE=/path/to/Chromium \
node task08_quantum_cryptography/app/tests/accessibility-audit.mjs
```

## Evidence summary

| WCAG criteria | Evidence | Result |
|---|---|---|
| 1.1.1, 1.3.1 | Eleven ordered headings, one main landmark, eighteen named controls, three titled and described SVG figures | Pass |
| 1.4.1 | Classical is labelled solid; quantum is labelled dashed; the selected-angle marker is labelled separately | Pass |
| 1.4.3 | Fourteen representative text/surface pairs; minimum tested ratio 4.60:1 | Pass |
| 1.4.4 | 200% root-text resize at 800 px without clipping or page-level horizontal overflow | Pass |
| 1.4.10 | 320 px page reflow without page overflow; only the intrinsically two-dimensional graph scrolls inside its named region | Pass |
| 1.4.11 | Button boundary and both graph curves tested; minimum essential non-text ratio 3.30:1 | Pass |
| 2.1.1 | All controls, presets, the graph viewport and the finite-photon experiment operate by keyboard; arrow keys change angles by one degree | Pass |
| 2.3.3 | Reduced-motion preference suppresses transitions | Pass |
| 2.4.1 | First tab stop is a working skip link that moves focus to the calculator | Pass |
| 2.4.3, 2.4.7 | All 20 focusable elements reached exactly once in DOM order with a visible 3 px outline | Pass |
| 3.3.2 | Angle, photon-count and seed inputs have explicit accessible instructions or names | Pass |
| 4.1.2 | Key headings, controls, meters and figures appear with names and values in the 550-node Chromium accessibility tree | Pass |
| 4.1.3 | Separate polite atomic statuses announce theoretical changes and user-triggered finite-sample changes without combining both messages | Pass |

## Remediation completed during Stage 5

- Added a visible-on-focus skip link and a focusable main target.
- Added explicit accessible names for both numeric angle fields and keyboard instructions for both sliders.
- Replaced broad result-region announcements with one concise polite status message.
- Added `aria-valuetext` to both probability meters.
- Made detector descriptions and the comparison-graph description update with the selected angles and values.
- Added a keyboard-focusable graph viewport for narrow screens and a visible scroll instruction.
- Darkened orange, teal, blue, muted text and interactive boundaries where required for AA contrast.
- Added solid/dashed graph encodings so colour is never the only model identifier.
- Added enhanced-contrast, forced-colour and reduced-motion styles.
- Added named photon-count and seed controls, keyboard-operable sample presets and a dedicated finite-sample status.
- Included the finite-photon cards, interval graphics and warnings in contrast, reflow and 200% text-resize checks.

## Visual review

The 1440 px desktop rendering and 390 px mobile rendering were inspected after the audit. The desktop graph is fully visible with clear axes, curves, legend and selected-angle markers. The mobile layout has no page-level overflow; the graph remains legible in a contained horizontal viewport with an explicit instruction rather than being compressed into unreadable labels.

## Repeatability

The accessibility audit is deterministic and fails on missing names, broken heading order, weak tested contrast, missing focus indicators, keyboard-order drift, graph-encoding regressions, page-level reflow, text clipping, missing live updates or disabled user display preferences.
