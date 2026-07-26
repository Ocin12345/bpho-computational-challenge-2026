# Task 10 Results and Interpretation

## Direct answer to the official task

The requested S–G probability densities are collected in
[the complete orbital gallery](../figures/task10/required_orbital_gallery.png).
It contains every allowed real magnetic state for 1s, 2p, 3d, 4f and 5g:

| Family | Frozen representative shell | Allowed \(m\) | States | Radial nodes | Angular nodes |
|---|---:|---:|---:|---:|---:|
| S | 1s | 0 | 1 | 0 | 0 |
| P | 2p | −1…+1 | 3 | 0 | 1 |
| D | 3d | −2…+2 | 5 | 0 | 2 |
| F | 4f | −3…+3 | 7 | 0 | 3 |
| G | 5g | −4…+4 | 9 | 0 | 4 |

The official gallery chooses \(n=l+1\), so each representative has no radial
node and exposes the angular structure of its family directly.

## Normalized hydrogenic model

For a nucleus of charge \(+Ze\), the effective Bohr length is

$$
a=\frac{m_e}{\mu}\frac{a_0}{Z},
\qquad
\mu=\frac{m_eM}{m_e+M},
$$

and the normalized radial function is

$$
R_{nl}(r)=
\sqrt{\frac{(n-l-1)!}{2n(n+l)!}}
\left(\frac{2}{na}\right)^{3/2}
e^{-\rho/2}\rho^lL_{n-l-1}^{2l+1}(\rho),
\qquad \rho=\frac{2r}{na}.
$$

The package combines this with normalized real tesseral harmonics
\(\mathcal Y_{lm}\):

$$
\psi_{nlm}=R_{nl}\mathcal Y_{lm},
\qquad
P(\mathbf r)=|\psi_{nlm}(\mathbf r)|^2,
\qquad
\int P(\mathbf r)\,dV=1.
$$

Positive and negative \(m\) select cosine and sine orientations of the same
real harmonic family. The density discards the sign of the wavefunction, so
nodal surfaces are visible but positive and negative phase lobes are not.

## Family energy and spatial anchors

For hydrogen-1 the five representative states are:

| State | Energy / eV | 99.95% radial extent / \(n^2a\) | Parity | \(m\) degeneracy |
|---|---:|---:|---:|---:|
| 1s | −13.598233405346 | 6.02570 | even | 1 |
| 2p | −3.399558351336 | 3.92748 | odd | 3 |
| 3d | −1.510914822816 | 3.17578 | even | 5 |
| 4f | −0.849889587834 | 2.77711 | odd | 7 |
| 5g | −0.543929336214 | 2.52556 | even | 9 |

The physical size grows approximately as \(n^2a\), even though the containment
extent becomes more compact when expressed in those scaled units. Energy depends
only on \(n\) and \(Z\) in the frozen point-Coulomb model:

$$
E_n=-\frac12E_h\frac{\mu}{m_e}\frac{Z^2}{n^2}.
$$

It is therefore independent of \(l\) and \(m\). This is the Coulomb degeneracy;
real atoms can split it through interactions deliberately excluded here.

## Nodes, parity and radial probability

The radial-node count is

$$
N_r=n-l-1,
$$

the angular-node count is \(N_\Omega=l\), and parity is \((-1)^l\). A 2s state
therefore has one radial node and no angular node, while a 3p state has one of
each. The 3d state in the coloured-glass construction has no radial nodes and
two angular nodes.

The radial graph displays

$$
P_r(r)=r^2|R_{nl}(r)|^2,
\qquad
\int_0^\infty P_r(r)\,dr=1.
$$

It is independent of \(m\). Changing \(m\) rotates or changes the angular
orientation of a real basis state without changing this radial profile.

## Scaling with nuclear charge

At fixed \(n,l,m\), energy magnitude scales as \(Z^2\) and length as \(1/Z\),
with a small isotope-dependent reduced-mass correction. For the 3d, \(m=0\)
state:

| Ion convention | \(Z\) | \(A\) | Energy / eV | Effective \(a\) / Å |
|---|---:|---:|---:|---:|
| H-1 | 1 | 1 | −1.510914822816 | 0.529467506530 |
| C-12 hydrogenic ion | 6 | 12 | −54.420284669061 | 0.088200233646 |
| Ca-40 hydrogenic ion | 20 | 40 | −604.689179124539 | 0.026459223397 |

The angular shape and scaled radial shape are unchanged. Only the physical
length and energy scales change.

## What each visual representation preserves

### Orthogonal slices

Slices retain quantitative density values on declared planes. They make node
cross-sections and relative brightness easy to compare, but they do not show the
complete three-dimensional topology between planes.

### Outer isosurface

An isosurface connects all points at one chosen relative density. It communicates
outer topology compactly but discards values both inside and outside that level;
an apparent boundary is a display choice, not the edge of an atom.

### Coloured-glass stack

The required stack preserves multiple internal planes simultaneously. Colour and
opacity encode relative density, allowing inner structure to remain visible.
Plane spacing, opacity and ordering can nevertheless cause occlusion. The 0.15
threshold changes visibility only; the normalized unthresholded field remains
the scientific result.

The threshold changes visibility only; it never changes the wavefunction.

### View rotation

The [4K motion artifact](../figures/task10/orbital_view_rotation.webp) rotates the
camera around one stationary hydrogen 3d eigenstate. It is not an orbital period,
electron trajectory, probability flow or time evolution. The exact decoded
quarter-turn frames are shown in the
[inspection sheet](../reports/task10/orbital_view_rotation_contact_sheet.png).
The camera movement is not electron motion.

## Independent numerical anchors

The accepted reference package includes:

- hydrogen 1s energy \(-13.598233405346\) eV;
- hydrogen effective Bohr length \(0.529467506530\) Å;
- scaled 1s density at the origin \(1/\pi=0.318309886184\);
- a zero 2s density at its analytic radial node \(r/a=2\);
- zero 2p\(_z\) density on the equatorial nodal plane;
- identical normalized p-axis amplitudes \(0.488602511903\) for the three real
  P orientations; and
- carbon-12 3d energy \(-54.420284669061\) eV.

All 22 independent science groups pass, including radial and angular
normalization, orthogonality, expectation values, node roots, parity and scaling.

## Figure-by-figure reading guide

1. [required_orbital_gallery](../figures/task10/required_orbital_gallery.png)
   is the direct 25-state official answer.
2. [radial_and_nodal_structure](../figures/task10/radial_and_nodal_structure.png)
   separates radial probability, containment and node structure.
3. [coloured_glass_density](../figures/task10/coloured_glass_density.png) is the
   required semitransparent construction.
4. [rendering_comparison](../figures/task10/rendering_comparison.png) explains
   what slices, an outer isosurface and coloured glass preserve or hide.
5. [task10_summary](../figures/task10/task10_summary.png) combines the central
   result in a 3840×2160 competition plate.
6. [orbital_view_rotation](../figures/task10/orbital_view_rotation_viewer.html)
   presents the accepted 4K loop with an automatic reduced-motion poster.

Every raster was inspected at original resolution. Editable SVG and
embedded-font PDF companions are provided where the representation is genuinely
vector-safe. Times New Roman is used consistently across every presentation
surface.

## Physical limitations

The model assumes one non-relativistic electron in an ideal point-Coulomb field.
It omits screening, electron-electron correlation, spin, spin-orbit coupling,
fine and hyperfine structure, radiative effects, finite nuclear size, external
fields, continuum states, ionization dynamics, measurement and detector
response. It also presents stationary basis states rather than arbitrary
time-dependent superpositions.

Within that scope, the wavefunctions are exact analytic Coulomb eigenfunctions;
the numerical work evaluates and validates them rather than approximating their
time evolution.
