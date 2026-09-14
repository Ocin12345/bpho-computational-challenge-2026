# Task 6 Relativistic Extension Acceptance

## Outcome

The optional relativistic precision comparison is implemented and accepted as
a secondary extension. It does not replace or modify the official
non-relativistic Task 6 calculation.

## Evidence

- 401 voltage records from 1 to 5 kV in exact 10 V increments;
- relativistic momentum from $K(K+2m_ec^2)=p^2c^2$;
- wavelength from $\lambda=h/p$;
- both wavelengths passed through the same exact Bragg and
  $x=r\sin(2\phi)$ geometry;
- first-order radius shifts for both 0.123 nm and 0.213 nm spacings;
- 10/10 focused extension checks; and
- deterministic, finite JSON generation with corruption detection.

At 1 kV, the relativistic wavelength correction is approximately
$-0.04889\%$. At 5 kV it is approximately $-0.24372\%$. At 5 kV, the
first-order rings move inward by approximately 43.02 µm for $d_1$ and
25.48 µm for $d_2$.

## Boundary

The extension quantifies a precision correction only. It does not add or imply
calibrated ring intensity, graphite structure factors, broadening, detector
response, or automatic physical time evolution.
