(() => {
  const root = document.documentElement;
  const gsap = window.gsap;
  const ScrollTrigger = window.ScrollTrigger;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  if (!gsap || !ScrollTrigger || reduceMotion.matches) {
    root.dataset.motionStatus = reduceMotion.matches ? "reduced" : "fallback";
    return;
  }

  gsap.registerPlugin(ScrollTrigger);
  root.dataset.motionStatus = "active";

  const entrance = gsap.timeline({
    defaults: { duration: 0.82, ease: "power3.out" },
  });

  entrance
    .from(".task-header", { yPercent: -100, duration: 0.58 })
    .from(".hero-copy > p", { y: 22 }, "-=0.25")
    .from(".hero-copy h1", { y: 42 }, "-=0.58")
    .from(".hero-copy > span", { y: 28 }, "-=0.63")
    .from(".state-laboratory", { x: 40 }, "-=0.7")
    .from(".hero-controls > *", { y: 24, stagger: 0.055 }, "-=0.52")
    .from(".catalogue-strip > *", { y: 18, stagger: 0.04 }, "-=0.48");

  const revealGroups = [
    {
      trigger: ".model-section",
      selectors: [
        ".model-section .section-introduction > *",
        ".equation-architecture article",
        ".boundary-statement > *",
      ],
      y: 34,
    },
    {
      trigger: ".spectrum-section",
      selectors: [
        ".spectrum-section .section-introduction > *",
        ".spectrum-laboratory",
        ".spectrum-notes article",
      ],
      y: 40,
    },
    {
      trigger: ".density-section",
      selectors: [
        ".density-section .section-introduction > *",
        ".density-controls",
        ".density-figure",
        ".density-laws p",
      ],
      y: 36,
    },
    {
      trigger: ".uncertainty-section",
      selectors: [
        ".uncertainty-section .section-introduction > *",
        ".moment-ledger article",
        ".uncertainty-figure",
        ".extension-actions > *",
      ],
      y: 40,
    },
    {
      trigger: ".numerical-section",
      selectors: [
        ".numerical-section .section-introduction > *",
        ".convergence-band article",
        ".accepted-figure",
      ],
      y: 35,
    },
    {
      trigger: ".evidence-section",
      selectors: [
        ".evidence-section > header > *",
        ".evidence-lock",
        ".evidence-grid article",
        ".evidence-downloads a",
      ],
      y: 32,
    },
  ];

  revealGroups.forEach(({ trigger, selectors, y }) => {
    const targets = selectors.flatMap((selector) =>
      gsap.utils.toArray(selector),
    );
    gsap.from(targets, {
      y,
      duration: 0.82,
      ease: "power3.out",
      stagger: 0.05,
      scrollTrigger: {
        trigger,
        start: "top 84%",
        once: true,
      },
    });
  });

  let pointerFrame = 0;
  function handlePointerMove(event) {
    if (window.innerWidth < 940) return;
    cancelAnimationFrame(pointerFrame);
    pointerFrame = requestAnimationFrame(() => {
      const x = (event.clientX / window.innerWidth - 0.5) * 6;
      const y = (event.clientY / window.innerHeight - 0.5) * 5;
      gsap.to(".hero-copy", {
        x,
        y,
        duration: 0.75,
        ease: "power2.out",
        overwrite: "auto",
      });
    });
  }

  window.addEventListener("pointermove", handlePointerMove, { passive: true });
  window.addEventListener("task07:ready", () => ScrollTrigger.refresh(), {
    once: true,
  });

  window.addEventListener(
    "pagehide",
    () => {
      cancelAnimationFrame(pointerFrame);
      window.removeEventListener("pointermove", handlePointerMove);
      entrance.kill();
      ScrollTrigger.getAll().forEach((trigger) => trigger.kill());
      gsap.killTweensOf("*");
    },
    { once: true },
  );
})();
