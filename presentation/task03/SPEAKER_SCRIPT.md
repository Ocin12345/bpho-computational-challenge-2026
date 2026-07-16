# Task 3 Speaker Script

## Final competition version — approximately 17–18 seconds

Use this version in the final three-minute video:

> Task 3 models Planck radiation and Einstein heat capacity. Increasing
> temperature moves the black-body peak to shorter wavelengths, while total
> emission follows T to the fourth. For solids, the Einstein temperature sets
> how quickly heat capacity rises towards three R. All twenty-seven analytical
> and numerical checks passed.

The equations and units remain visible and do not need to be read aloud in the
competition version.

### Visual cues

| Time | What to show or indicate | Words being spoken |
| --- | --- | --- |
| $0$--$7$ s | Indicate the three Planck curves and their marked peaks | “Task 3 models … T to the fourth.” |
| $7$--$14$ s | Move to the Einstein curves and dashed $3R$ line | “For solids … towards three R.” |
| $14$--$18$ s | Indicate the green validation badge | “All twenty-seven … checks passed.” |

Do not try to name all seven materials during the final version. Their labels
are already visible, and doing so would hide the main comparison.

## Expanded version — approximately 35 seconds

Use this only if the final video plan gives Task 3 additional time:

> For Task 3, I calculated Planck spectral exitance at 4000, 5000 and 6000
> kelvin. As temperature increases, the peak shifts from 724 to 483
> nanometres, following Wien's displacement law, while the integrated power
> follows the Stefan--Boltzmann T-to-the-fourth law. I then calculated
> Einstein molar heat capacities for all seven supplied solids. Materials with
> a lower Einstein temperature approach the classical three-R limit sooner;
> carbon rises more slowly because its Einstein temperature is much higher.
> Normalizing by three R and the Einstein temperature collapses all seven
> curves, and all twenty-seven validation checks pass.

## Detailed rehearsal version — approximately 90 seconds

This version is for understanding and practice. It is too long for the final
three-minute video if all ten tasks must be included.

> Task 3 contains two deterministic quantum models rather than a random
> simulation. First, I evaluated Planck's law for ideal black bodies at 4000,
> 5000 and 6000 kelvin. The plotted quantity is spectral exitance per
> nanometre, so integrating the complete curve gives emitted power per unit
> surface area. As temperature increases, each curve becomes taller and its
> maximum moves to a shorter wavelength. The numerical peaks are 724, 580 and
> 483 nanometres. They agree with Wien's inverse-temperature law, and the
> integrated spectra agree with the Stefan--Boltzmann T-to-the-fourth law.
>
> Second, I evaluated Einstein's constant-volume molar heat-capacity model for
> the seven solids in the official table. The model treats each material as
> one oscillator frequency. Its heat capacity is exactly zero at zero
> temperature and approaches the classical Dulong--Petit limit, three R, at
> sufficiently high temperature. A lower Einstein temperature means the curve
> rises sooner, so gold is close to three R by room temperature. Carbon has an
> Einstein temperature near 1797 kelvin and therefore remains well below the
> limit at 800 kelvin.
>
> When I plot heat capacity divided by three R against temperature divided by
> the Einstein temperature, all seven curves collapse onto one universal
> function. This confirms that material identity only sets the temperature
> scale inside this model. The complete validation contains twenty-seven
> passing checks, including the Wien and Stefan--Boltzmann laws, exact physical
> bounds, the high-temperature limit and all seven official frequencies.
>
> The main limitation is that real crystals contain a range of vibrational
> frequencies. Einstein's one-frequency model therefore misses the Debye
> T-cubed low-temperature behaviour and predicts constant-volume rather than
> constant-pressure heat capacity.

## Pronunciation guide

| Term | Say it as |
| --- | --- |
| Planck | “plank” |
| Wien | “veen” |
| Stefan--Boltzmann | “SHTEF-an BOLTZ-man” |
| Einstein | “EYE-n-stine” |
| $T_E$ | “Einstein temperature” or “T E” |
| $C_V$ | “C V” or “constant-volume heat capacity” |
| $3R$ | “three R” |
| $T^4$ | “T to the fourth” |
| $T^3$ | “T cubed” |
| $8.33\times10^{-6}$ | “eight point three three times ten to the minus six” |
| Dulong--Petit | “doo-LONG puh-TEE” |

## Questions you should be ready to answer

**Why does the main graph say spectral exitance rather than radiance?**

The official equation is the spectral radiance $B_{\lambda}$, measured per
steradian. For an ideal Lambertian black body, hemispherical spectral exitance
is $M_{\lambda}=\pi B_{\lambda}$. We plot exitance because its wavelength
integral is directly $\sigma T^4$ in watts per square metre.

**Why does the Planck peak move to shorter wavelengths?**

Wien's displacement law gives $\lambda_{\max}T=b$. Peak wavelength is therefore
inversely proportional to absolute temperature. Increasing temperature from
$4000$ to $6000\ \mathrm K$ divides the peak wavelength by $1.5$.

**Why does the total emitted power increase as $T^4$?**

Integrating Planck's spectral exitance over all wavelengths produces the
Stefan--Boltzmann law $M=\sigma T^4$. This law concerns the total area under the
complete spectrum, not the height at one wavelength.

**Why are the Einstein curves different for each material?**

The model depends on $T/T_E$. A material with a larger Einstein temperature
has a larger assumed vibrational energy quantum, so more thermal energy is
needed before its heat capacity rises towards $3R$.

**Why has carbon not reached $3R$ at $800\ \mathrm K$?**

Carbon's calculated Einstein temperature is about $1797\ \mathrm K$. The
display maximum is therefore only about $0.45T_E$, not the high-temperature
regime. A separate validation at $100T_E$ confirms the $3R$ limit to a relative
error of $8.33\times10^{-6}$.

**Why do the normalized curves collapse?**

Dividing temperature by $T_E$ and heat capacity by $3R$ removes every material
parameter from the Einstein equation. The maximum separation of the seven
stored curves is $8.88\times10^{-16}$, so the collapse is numerical as well as
analytical.

**Is the model predicting $C_P$ or $C_V$?**

It predicts constant-volume molar heat capacity, $C_V$. Experimental tables
often quote $C_P$, which can differ because real solids expand when heated.

**What is the most important limitation?**

Einstein assigns one vibrational frequency to every atom in a material. Real
crystals have a spectrum of modes, including low-frequency acoustic modes. The
Debye model represents those modes and gives the more realistic low-temperature
$T^3$ law; Einstein instead predicts an exponential decrease.

**How do you know the figures are calculated correctly?**

The 27 pre-declared checks test finite and non-negative spectra, the factor of
$\pi$ between radiance and exitance, Wien peak positions, both Planck
integrals, the Einstein zero and high-temperature limits, physical bounds,
monotonicity, all seven official frequencies and normalized collapse. All
checks pass without changing their tolerances.

**Why are repeated simulations or a GPU unnecessary?**

Both models are deterministic equations evaluated on fixed numerical grids.
There is no randomness, particle time-stepping or fitted optimization. A
vectorized NumPy calculation on the MacBook Air completes comfortably within
the declared time budget.

**Is the $6000\ \mathrm K$ curve meant to be the measured solar spectrum?**

No. It is an ideal black-body spectrum used to show temperature dependence.
The model omits solar absorption lines, atmospheric transmission, geometric
dilution and detector response.
