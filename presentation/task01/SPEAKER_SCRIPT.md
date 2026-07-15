# Task 1 Speaker Script

## Final competition version — approximately 16–17 seconds

Use this version in the final three-minute video:

> For Task 1, I modelled fixed-length steps with directions sampled uniformly
> from zero to two pi. Fifty walks show no preferred direction. Fifty thousand
> simulations per step count gave a mean squared displacement slope of 0.9992,
> matching the theoretical value of one.

### Visual cues

| Time | What to show or indicate | Words being spoken |
| --- | --- | --- |
| 0–5 s | Entire slide, then the model text | “For Task 1 … zero to two pi.” |
| 5–9 s | Point to the 50-walk image | “Fifty walks … direction.” |
| 9–17 s | Point to the result box and endpoint cloud | “Fifty thousand … value of one.” |

Do not rush the number **0.9992**. Say it as “zero point nine nine nine two.”

## Expanded version — approximately 30 seconds

Use this only if the final video plan allows more time for Task 1:

> For Task 1, I generated $N$ fixed-length steps. At every step, the angle
> theta is sampled uniformly from zero to two pi, and I update the coordinates
> using $s\cos\theta$ and $s\sin\theta$. Fifty independent walks show no
> preferred direction. Testing fifty thousand walks at each step count gave a
> mean squared displacement slope of 0.9992 plus or minus 0.0031, which agrees
> with the theoretical value of one.

## Detailed rehearsal version — approximately 70 seconds

This version is for understanding and practice. It is too long for the final
three-minute competition video if all ten tasks must be shown.

> Task 1 asks for a two-dimensional random walk made from $N$ steps, each
> exactly length $s$. For every step, I generate an independent angle theta
> from a uniform distribution between zero and two pi. I then calculate the
> displacement components: delta x equals $s\cos\theta$, and delta y equals
> $s\sin\theta$. Cumulatively adding these displacements produces the path.
>
> The first figure overlays fifty independent 1,000-step walks. They spread in
> every direction, so there is no visual evidence of drift. However, a graph
> alone is not sufficient evidence, so I tested fifty thousand walks at each of
> eight values of $N$. This represents 400,000 complete walks and 194 million
> simulated steps.
>
> Theory predicts zero mean horizontal and vertical displacement, equal
> coordinate variances, and mean squared displacement equal to $Ns^2$. The
> fitted slope was 0.9992 plus or minus 0.0031 at 95 percent confidence, which
> includes the theoretical value of one. The circular endpoint cloud and its
> radial containment results also agree with theory. This verifies that the
> numerical model is fixed-step, unbiased, and isotropic.

## Pronunciation guide

| Term | Say it as |
| --- | --- |
| $\theta$ | “theta” |
| $2\pi$ | “two pie” |
| $s\cos\theta$ | “s times cosine theta” |
| $Ns^2$ | “N s squared” |
| MSD | “mean squared displacement” |
| $\pm$ | “plus or minus” |
| isotropic | “eye-so-TROP-ik” |

## Questions you should be ready to answer

**Why generate an angle instead of random x and y changes?**

Generating the angle first guarantees that every step has exactly the required
length $s$.

**Why does one path not prove that the model is unbiased?**

One random path can finish anywhere. Bias is tested using the mean endpoints of
many independent walks.

**What is the main theoretical result?**

The mean squared displacement is $Ns^2$, so the RMS displacement grows as
$s\sqrt{N}$, rather than linearly with $N$.

**Does every walk finish at the RMS distance?**

No. RMS displacement is an ensemble statistic, and individual endpoints vary.

**Why use a fixed seed?**

It makes the figures exactly reproducible. Changing the seed changes the
individual paths but not the predicted statistics.
