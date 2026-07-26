# Task 7 Official Requirements

## Authoritative sources

The detailed Task 7 brief occupies PDF pages 48–49 of
`BPhO CompPhys2026 Quantum.pdf`, contained in the official
[2026 course and challenge materials ZIP](https://www.bpho.org.uk/bpho/computational-challenge/BPhO_ComPhys_Challenge_2026.zip).
Page 47 supplies the infinite-well formula immediately before the challenge,
and page 49 directs entrants to Question 2 of the supplied Quantum Mechanics 3
problem sheet for the uncertainty-principle extension. The concise competition
summary appears on page 3 of the
[2026 challenge specification](https://www.bpho.org.uk/bpho/computational-challenge/BPhO_ComPhys_Challenge_2026.pdf).

The source files inspected on 18 July 2026 had the following byte sizes and
SHA-256 digests:

| Official file | Size | SHA-256 |
|---|---:|---|
| `BPhO_ComPhys_Challenge_2026.zip` | 32,210,979 bytes | `330bffb2b7424cf0faada630aed39515cca32fcfee2dcf2096c218144498c667` |
| `BPhO CompPhys2026 Quantum.pdf` extracted from the ZIP | 10,739,932 bytes | `7948f13c88d09a7ec2d94a564fcd7b085419090320c011575c851edb6db151c6` |
| `BPhO_ComPhys_Challenge_2026.pdf` | 867,675 bytes | `e40a22145b96591aad32221e97035662228dadd09ff9e31562ce6b16da3202ff` |

The large downloaded source files are deliberately kept outside the repository.
Their recorded hashes allow the interpretation below to be checked against the
same frozen official material.

## Required outcome

For a particle in a one-dimensional infinite potential well, Task 7 asks for:

1. energy plotted against the integer quantum number (n); and
2. probability densities (|\psi_n(x)|^2) plotted against displacement (x)
   inside the box.

The supplied model is

$$
V(x)=
\begin{cases}
0,&0<x<a,\\
\infty,&x\leq0\text{ or }x\geq a,
\end{cases}
$$

with normalized stationary states and energies

$$
\psi_n(x,t)=\sqrt{\frac{2}{a}}
\sin\!\left(\frac{n\pi x}{a}\right)e^{-iE_nt/\hbar},
\qquad
E_n=\frac{n^2\pi^2\hbar^2}{2ma^2}.
$$

The brief does not freeze a unique mass or box width for the submitted plots.
This project therefore uses a disclosed, configurable baseline: one electron in
a (1.00\ \mathrm{nm}) box. Normalized coordinates and scaled density
(a|\psi|^2) make the state shapes independent of that illustrative choice.

## Official extension

The extension asks for a LaTeX write-up of the particle-in-a-box model and a
demonstration that position and momentum obey Heisenberg's uncertainty relation,

$$
\Delta x\,\Delta p\geq\frac{\hbar}{2}.
$$

The accepted extension must calculate (\langle x\rangle),
(\langle x^2\rangle), (\langle p\rangle) and (\langle p^2\rangle), form
the two standard deviations, and establish the inequality for positive integer
(n). Question 2 of the supplied Quantum Mechanics 3 sheet is the official
derivation anchor.

## Frozen success criteria

- Treat (n) as a discrete positive integer and do not imply allowed energies
  between the plotted states.
- Enforce (\psi(0)=\psi(a)=0), normalized wavefunctions and (n-1) interior
  nodes.
- Distinguish signed wavefunction amplitude from non-negative probability
  density.
- Label physical or normalized axes unambiguously and preserve unit consistency.
- Show the (n^2) energy law and the first four official density examples
  clearly enough for the final screencast.
- Complete the uncertainty extension analytically, including the strict
  ground-state result (\Delta x\Delta p/\hbar\approx0.567862>1/2).
- Validate the analytical result independently rather than using it as its own
  sole numerical reference.
- Provide local, reproducible code, data, figures, report source and presentation
  evidence.

## Scope boundary

The required system is an ideal, one-dimensional, non-relativistic,
single-particle infinite well. Finite barriers, tunnelling, interactions, spin,
external fields, higher dimensions and time-dependent superpositions are not
required. A single stationary state's probability density is time independent;
an animation that implied particle motion would therefore be misleading unless
a separately declared superposition or wave packet were introduced.
