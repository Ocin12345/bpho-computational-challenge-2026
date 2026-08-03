# BPhO Computational Challenge website

This directory contains the static public-facing website for the 2026 BPhO
Computational Challenge project. It includes the landing page, the ten-task
index, individual pages for Tasks 1–10, and the interactive laboratory views.

## Preview locally

From the repository root:

```bash
python3 -m http.server 8080
```

Then open:

```text
http://localhost:8080/site/
```

The opening page uses a procedural Three.js fragment shader rather than a
background image. The task pages provide browser-based visualisations,
calculators, evidence panels, and links back to the validated Python work.

The opening page includes:

- an animated loading sequence;
- a pointer-responsive wavefunction and interference field;
- a reduced-motion mode and WebGL fallback;
- responsive desktop and mobile typography;
- one minimal live/pause control.

Three.js is loaded as an ES module from jsDelivr, so the landing page needs an
internet connection for that module. The task pages use the pinned local
runtime files under `vendor/packages`.

The files under `vendor/packages` are tracked because the static pages load
them directly. The `vendor/package.json` and `vendor/package-lock.json` files
record the pinned dependency versions. Local `vendor/node_modules` installs
and downloaded `vendor/archives` caches are intentionally excluded from Git.
