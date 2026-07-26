# Task 6 Speaker Script

## Final competition version

> Task 6 models electrons accelerated through one to five kilovolts. Higher
> voltage shortens their de Broglie wavelength, changing the graphite
> diffraction rings. Using exact spherical geometry and both graphite
> spacings, the required one-over-root-V graph is perfectly linear and
> recovers 0.123 and 0.213 nanometres. All thirty-nine independent checks
> pass.

### Visual cues

- **0--6 seconds:** point to the 1, 3, and 5 kV ring comparison.
- **6--14 seconds:** follow the two straight lines in the required graph.
- **14--18 seconds:** finish on the recovered spacings and validation badge.

## Expanded 35-second version

> Task 6 accelerates electrons through one to five kilovolts, so their de
> Broglie wavelength falls from 38.8 to 17.3 picometres. Bragg's law gives the
> scattering angle for two graphite plane spacings, and the exact spherical
> geometry converts that angle to a photographic ring radius. The required
> one-over-square-root-voltage graph is linear for each spacing. Its gradients
> recover 0.123 and 0.213 nanometres, both with R squared equal to one. The
> model stores all Bragg orders but displays only those on the forward screen.

## Rehearsal explanation

An electron accelerated through potential difference $V$ gains kinetic energy
$eV$. In the official non-relativistic model this gives momentum
$p=\sqrt{2m_{\mathrm e}eV}$ and wavelength
$\lambda=h/p$. Therefore the wavelength decreases as $V^{-1/2}$.

Bragg's law is $2d\sin\theta=n\lambda$. The scattering angle is
$\phi=2\theta$, so $\sin(\phi/2)=n\lambda/(2d)$. The photographic geometry in
the written brief is $x=r\sin(2\phi)$. The separate expression
$y=2r\sin\phi$ is a full caliper chord and is not substituted for $x$.

The complete data catalogue retains every order with Bragg ratio below unity.
The ring rendering shows the forward-screen subset with
$\phi\leq90^\circ$. Brightness is schematic because the challenge does not
supply graphite structure factors, crystallite size, beam spread, or phosphor
response.

## Pronunciation guide

| Term | Say it as |
| --- | --- |
| de Broglie | “duh BROY” |
| Bragg | “brag” |
| $\lambda$ | “lambda” |
| $\phi$ | “fye” |
| $1/\sqrt V$ | “one over square root V” |
| $0.123\ \mathrm{nm}$ | “zero point one two three nanometres” |

## Questions you should be ready to answer

**Why do the first-order rings contract as voltage rises?**

Higher voltage increases momentum and reduces wavelength. For fixed $d$ and
$n$, Bragg's law then gives a smaller scattering angle and a smaller
first-order projected radius over the studied range.

**Why are there two ring families?**

The graphite geometry provides at least two nominal layer spacings, 0.123 and
0.213 nanometres. Each spacing gives a separate Bragg-angle sequence.

**Why are Bragg maximum and screen maximum different?**

The Bragg condition allows ratios up to unity, including back-scattering
solutions. The pictured phosphor screen occupies the forward hemisphere, so
displayed rings also require $\phi\leq90^\circ$.

**Does the model predict which rings are bright?**

No. It predicts ideal geometric positions. Quantitative intensity needs
structure factors and experimental response data that were not supplied.

**How was the atomic spacing recovered?**

For fixed order, plotting $1/\sqrt V$ against $\sin(\phi/2)$ gives a line
through the origin. Substituting its gradient into the rearranged Bragg and de
Broglie equations returns $d$.
