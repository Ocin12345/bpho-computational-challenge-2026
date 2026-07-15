# Text to Put on the Task 1 Slide

## Title

**Task 1 — Two-Dimensional Random Walk**

## Result box

Use only these three lines on the slide:

```text
Direction: θ uniformly sampled from 0 to 2π
Theory: ⟨r²⟩ = Ns²
Simulation: MSD slope = 0.9992 ± 0.0031 (95% CI)
```

If PowerPoint's equation editor is available, the mathematical versions are:

```text
\theta \sim \mathrm{Uniform}(0,2\pi)
\langle r^2\rangle = Ns^2
\text{MSD slope}=0.9992\pm0.0031
```

## Optional small caption

```text
50,000 independent walks at each of eight step counts
```

Do not add the full method or conclusion to the visible slide. Those details
belong in the narration and speaker notes.

## Accessibility text for the images

**50-walk image:** Fifty independent 1,000-step random walks begin at the
origin and spread in all directions without a preferred axis.

**Endpoint image:** Fifty thousand simulated endpoints form an approximately
circular density cloud around the origin and closely match the theoretical 50%
and 95% containment circles.
