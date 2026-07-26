# Task 8 Official Requirements

## Source

The scope is taken from pages 53--58 of the official 2026 BPhO Computational
Challenge presentation in the
[competition materials ZIP](https://www.bpho.org.uk/bpho/computational-challenge/BPhO_ComPhys_Challenge_2026.zip).

The accepted source files are frozen as follows:

| File | Size | SHA-256 |
|---|---:|---|
| `BPhO_ComPhys_Challenge_2026.zip` | 32,210,979 bytes | `330bffb2b7424cf0faada630aed39515cca32fcfee2dcf2096c218144498c667` |
| `BPhO CompPhys2026 Quantum.pdf` | 10,739,932 bytes | `7948f13c88d09a7ec2d94a564fcd7b085419090320c011575c851edb6db151c6` |

The page range, archive digest and extracted quantum-PDF digest are copied into
the generated core-data manifest so the implementation remains tied to this
specific official brief.

## Required outcome

Build a visual calculator comparing the classical and quantum probabilities
that the two photon-polarisation detectors produce different outcomes. The
detector angles \(\theta\) and \(\phi\) must be user-controlled variables. The
brief suggests sliders or gesture controls and explicitly allows a spreadsheet,
GUI or app.

The calculator must evaluate

$$
P_{\mathrm C}(\mathrm{mismatch})
=1-\cos^2\theta\cos^2\phi-\sin^2\theta\sin^2\phi
$$

and

$$
P_{\mathrm Q}(\mathrm{mismatch})=\sin^2(\phi-\theta).
$$

## Official reference case

For \(\theta=-30^\circ\) and \(\phi=30^\circ\), the presentation gives

$$
P_{\mathrm C}=\frac38=0.375,
\qquad
P_{\mathrm Q}=\frac34=0.750.
$$

This exact case is the default calculator state, a named preset and a mandatory
validation anchor.

## Frozen success criteria

- Both angles can be varied independently.
- Both mismatch probabilities update immediately and remain on a common scale.
- The detector orientations and angle difference are visible.
- Values are available as both probabilities and percentages.
- The official reference case is reproduced exactly within numerical tolerance.
- The calculator works locally without relying on an external account or service.
- The result is readable enough to demonstrate in the final screencast.

The required output is a comparison calculator. A full implementation of a
quantum-key-distribution protocol is outside the official Task 8 scope.
