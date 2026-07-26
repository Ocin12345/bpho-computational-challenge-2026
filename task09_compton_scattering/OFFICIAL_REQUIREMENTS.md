# Task 9 official requirements

## Authoritative source

The detailed Task 9 brief is on PDF pages 60–61 of
`BPhO CompPhys2026 Quantum.pdf`, contained in the official
[2026 course and challenge materials ZIP](https://www.bpho.org.uk/bpho/computational-challenge/BPhO_ComPhys_Challenge_2026.zip).
The companion
[competition specification](https://www.bpho.org.uk/bpho/computational-challenge/BPhO_ComPhys_Challenge_2026.pdf)
establishes the wider submission and award requirements.

The source files inspected on 17 July 2026 had the following SHA-256 digests:

| Official file | Size | SHA-256 |
|---|---:|---|
| `BPhO_ComPhys_Challenge_2026.zip` | 32,210,979 bytes | `330bffb2b7424cf0faada630aed39515cca32fcfee2dcf2096c218144498c667` |
| `BPhO CompPhys2026 Quantum.pdf` extracted from the ZIP | 10,739,932 bytes | `7948f13c88d09a7ec2d94a564fcd7b085419090320c011575c851edb6db151c6` |

Large downloaded source files remain outside the repository, as required by the
project policy.

## Required outcome

For Compton scattering of an incident X-ray photon from an initially stationary,
free electron, plot all three of the following quantities against photon
scattering angle $\theta$:

1. fractional photon wavelength shift $\Delta\lambda/\lambda$;
2. electron recoil speed $v$; and
3. electron recoil angle $\phi$.

The official example evaluates several incident photon energies on the full
$0^\circ$–$180^\circ$ angular range:

$$
E\in\{50,100,200,500,1000\}\ \mathrm{keV}.
$$

This five-energy set is therefore frozen as the primary Task 9 study. Additional
energies may be supported interactively, but must not replace these reference
curves.

## Equations supplied by the brief

The Compton wavelength shift is

$$
\Delta\lambda
=\lambda'-\lambda
=\frac{h}{m_e c}\left(1-\cos\theta\right),
$$

with incident photon wavelength $\lambda=hc/E$. The supplied recoil-speed form is

$$
v=c\sqrt{1-
\left(
\frac{m_e c^2}
{hc/\lambda-hc/\lambda'+m_e c^2}
\right)^2},
$$

and the supplied recoil-angle relation is

$$
\tan\phi=
\frac{\sin\theta}
{1+\dfrac{h}{m_e c\lambda}(1-\cos\theta)-\cos\theta}.
$$

The implementation must preserve the relativistic speed calculation. A
non-relativistic approximation is not sufficient for the 500 and 1000 keV
curves.

## Frozen success criteria

- Use photon scattering angle $\theta$ from $0^\circ$ to $180^\circ$ inclusive.
- Plot the required five incident energies and identify every curve clearly.
- Use one common energy colour mapping across all three required plots.
- Report fractional wavelength shift as a dimensionless quantity.
- Report recoil speed as both $v/c$ and, where useful, SI speed.
- Report recoil angle $\phi$ in degrees with an explicit sign/orientation
  convention.
- Treat $\theta=0^\circ$ honestly: the electron speed and momentum are zero, so
  its direction is physically undefined even though the continuous
  $\theta\rightarrow0^+$ limit of $\phi$ is $90^\circ$.
- Validate the supplied equations against independently derived energy–momentum
  relations and exact limiting cases.
- Keep every plotted probability-free kinematic quantity on an honest labelled
  scale with units and without smoothing or manually transcribed values.
- Produce local, reproducible, screencast-readable evidence at the same high
  visual standard as the preceding tasks.

## Scope boundary

The required task is a deterministic two-body kinematics study. A differential
cross-section, detector response, bound-electron correction, Doppler broadening,
multiple scattering or Monte Carlo event generator would be an optional extension
and must remain clearly separate from the required curves.

The core model assumes one photon scattering from one free electron initially at
rest. It does not describe photoelectric absorption, pair production, electron
binding in matter or a complete experimental apparatus.
