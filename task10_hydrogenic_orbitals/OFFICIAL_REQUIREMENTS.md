# Task 10 Official Requirements

## Authoritative source

The Task 10 brief occupies PDF pages 62–76 of
`BPhO CompPhys2026 Quantum.pdf`, contained in the official
[2026 course and challenge materials ZIP](https://www.bpho.org.uk/bpho/computational-challenge/BPhO_ComPhys_Challenge_2026.zip).
The companion
[competition specification](https://www.bpho.org.uk/bpho/computational-challenge/BPhO_ComPhys_Challenge_2026.pdf)
establishes the wider submission and award requirements.

The source files inspected on 17 July 2026 have the following SHA-256 digests:

| Official file | Size | SHA-256 |
|---|---:|---|
| `BPhO_ComPhys_Challenge_2026.zip` | 32,210,979 bytes | `330bffb2b7424cf0faada630aed39515cca32fcfee2dcf2096c218144498c667` |
| `BPhO CompPhys2026 Quantum.pdf` | 10,739,932 bytes | `7948f13c88d09a7ec2d94a564fcd7b085419090320c011575c851edb6db151c6` |

The downloaded source files remain outside the repository in accordance with the
project policy.

## Exact challenge statement

Task 10 asks for the mathematical recipe on the following slides to be used for
the wavefunctions of a hydrogenic atom—one electron orbiting a nucleus containing
\(Z\) protons—and for maps of the probability density to be plotted for selected
quantum numbers \(n,l,m\).

The primary calculated quantity is

$$
\rho_{nlm}(\mathbf r)=|\psi_{nlm}(\mathbf r)|^2,
\qquad
\psi_{nlm}(r,\vartheta,\varphi)
=R_{nl}(r)\,\mathcal Y_{lm}(\vartheta,\varphi).
$$

## Quantum-number domain

All selectable states must satisfy

$$
n\in\{1,2,3,\ldots\},
\qquad
l\in\{0,\ldots,n-1\},
\qquad
m\in\{-l,\ldots,+l\}.
$$

The orbital-family labels shown in the brief are:

| \(l\) | Family | First allowed \(n\) | Allowed \(m\) |
|---:|:---:|---:|---|
| 0 | S | 1 | 0 |
| 1 | P | 2 | −1, 0, +1 |
| 2 | D | 3 | −2, −1, 0, +1, +2 |
| 3 | F | 4 | −3 through +3 |
| 4 | G | 5 | −4 through +4 |

The official examples show the complete S–G sequence. The required implementation
must therefore include at least \(1\leq n\leq5\), all valid \(l\leq4\), and every
valid \(m\) in that range. A wider interactive range may be added only after this
official gallery is correct and remains accessible.

## Radial model supplied by the brief

Using reduced mass

$$
\mu=\frac{m_eM}{m_e+M},
$$

the brief defines the hydrogenic length scale

$$
a=\frac{m_ea_0}{\mu Z},
\qquad
x=\frac{2r}{an},
$$

and the radial wavefunction

$$
R_{nl}(r)
=
\sqrt{\frac{(n-l-1)!}{2n(n+l)!}}
\left(\frac{2}{an}\right)^{3/2}
x^l e^{-x/2}\,
L_{n-l-1}^{2l+1}(x).
$$

The associated Laguerre polynomial is written on the slide as

$$
L_{n-l-1}^{2l+1}(x)
=
\sum_{k=0}^{n-l-1}
\frac{(n+l)!(-x)^k}
{(2l+1+k)!(n-l-1-k)!k!}.
$$

The bound-state energy is

$$
E_n=-\frac{\mu e^4Z^2}{8\epsilon_0^2h^2n^2}.
$$

## Angular model and real orbitals

The brief introduces complex spherical harmonics

$$
Y_l^m(\vartheta,\varphi)
=(-1)^m
\sqrt{\frac{2l+1}{4\pi}\frac{(l-m)!}{(l+m)!}}\,
P_l^m(\cos\vartheta)e^{im\varphi}
$$

and combines the \(+m\) and \(-m\) solutions to make real orbital shapes. The
implementation will use normalized real tesseral harmonics:

$$
\mathcal Y_{lm}=
\begin{cases}
\sqrt2\,(-1)^m\operatorname{Im}Y_l^{|m|}, & m<0,\\
Y_l^0, & m=0,\\
\sqrt2\,(-1)^m\operatorname{Re}Y_l^m, & m>0.
\end{cases}
$$

This adds the normalization factors omitted by the slide's shape-only recipe.
Overall signs and rotations within a degenerate \(m\) subspace do not change
\(|\psi|^2\), but the adopted basis and orientation must be stated and kept
stable across Python, JavaScript, figures and animation.

## Coordinate convention

The official slides reuse \(\theta\) and \(\phi\) inconsistently between the
spherical-harmonic and Cartesian-conversion panels. To prevent a silent axis
swap, this project freezes the standard physics convention:

$$
x=r\sin\vartheta\cos\varphi,\qquad
y=r\sin\vartheta\sin\varphi,\qquad
z=r\cos\vartheta,
$$

where \(\vartheta\in[0,\pi]\) is polar colatitude and
\(\varphi\in(-\pi,\pi]\) is azimuth.

## Required visual outcome

The accepted Task 10 package must provide:

1. probability-density maps for valid \(n,l,m\);
2. clear physical axes and a length scale in ångströms and/or effective Bohr
   radii;
3. direct evidence of both the radial and angular parts of the wavefunction;
4. the S, P, D, F and G families shown in the official brief;
5. a genuinely three-dimensional visualization, not only a single 2D slice; and
6. a screencast-readable summary suitable for the final competition video.

The brief specifically encourages a “coloured glass” construction: semitransparent
\(x\)-\(y\) planes at fixed \(z\), colour-coded by \(|\psi|^2\). This will be the
primary 3D required view. Orthogonal slices and density isosurfaces may support it
but must not replace it.

The example pages display only points for which

$$
\frac{|\psi|^2}{\max|\psi|^2}\geq0.15.
$$

That 0.15 cutoff is a visualization threshold, not a physical boundary. The full
calculated grid must be retained; the threshold must be labelled, adjustable in
the explorer, and excluded from normalization calculations.

## Frozen success criteria

- Reject invalid triples rather than silently changing \(n,l,m\).
- Use exact normalized radial and real-angular functions.
- Confirm \(\int|\psi|^2\,d^3r=1\) independently for every acceptance state.
- Reproduce analytic 1s, 2s, 2p and representative D/F/G shapes and nodes.
- Verify \(n-l-1\) radial nodes and the expected angular nodal structure.
- Verify the \(Z^2/n^2\) energy scaling and the \(1/Z\) length scaling, including
  reduced-mass corrections.
- Keep absolute density and display-normalized density distinct in data, labels
  and documentation.
- Use stable colour, opacity, domain and camera conventions for valid visual
  comparisons.
- Do not infer orbital phase from a probability-density-only colour scale; if
  signed phase is shown, label it as a separate quantity.
- Produce deterministic data, publication PNG/SVG figures, a 4K summary, high-
  quality motion output, an offline explorer and a validated presentation.
- Include numerical, visual, browser, performance and accessibility acceptance
  evidence.

## Scope boundary

The required model is the non-relativistic one-electron Coulomb problem. It does
not include electron–electron interaction, fine structure, Lamb shift, spin,
Zeeman or Stark effects, nuclear finite size, radiative transitions, molecular
orbitals, chemical bonding or time-dependent superpositions.

Those effects must not be implied by the required static density maps. Any
extension must remain visibly separate from the normalized hydrogenic core.
