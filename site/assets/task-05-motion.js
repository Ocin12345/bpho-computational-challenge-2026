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
  root.classList.add("motion-ready");

  const entrance = gsap.timeline({
    defaults: { duration: 0.82, ease: "power3.out" },
  });

  entrance
    .from(".task-header", { yPercent: -100, duration: 0.62 })
    .from(".hero-copy > p", { y: 24 }, "-=0.28")
    .from(".hero-copy h1", { y: 40 }, "-=0.59")
    .from(".hero-copy > span", { y: 27 }, "-=0.62")
    .from(".transition-instrument", { x: 38 }, "-=0.7")
    .from(".hero-controls > *", { y: 24, stagger: 0.07 }, "-=0.54")
    .from(".catalogue-strip > *", { y: 19, stagger: 0.045 }, "-=0.5");

  const revealGroups = [
    {
      trigger: ".model-section",
      selectors: [
        ".model-section .section-introduction > *",
        ".equation-architecture article",
        ".energy-story > div",
        ".model-boundary",
      ],
      y: 34,
    },
    {
      trigger: ".atlas-section",
      selectors: [
        ".atlas-section .section-introduction > *",
        ".emission-atlas",
      ],
      y: 42,
    },
    {
      trigger: ".balmer-section",
      selectors: [
        ".balmer-section .section-introduction > *",
        ".balmer-instrument",
      ],
      y: 38,
    },
    {
      trigger: ".convergence-section",
      selectors: [
        ".convergence-section .section-introduction > *",
        ".limit-figure",
        ".limit-row",
      ],
      y: 38,
    },
    {
      trigger: ".evidence-section",
      selectors: [
        ".evidence-section .section-introduction > *",
        ".evidence-metrics > div",
        ".evidence-figures figure",
        ".evidence-lock",
      ],
      y: 34,
    },
    {
      trigger: ".extension-decision",
      selectors: [
        ".extension-decision .section-introduction > *",
        ".decision-ledger > div",
      ],
      y: 36,
    },
  ];

  revealGroups.forEach(({ trigger, selectors, y }) => {
    const targets = selectors.flatMap((selector) =>
      gsap.utils.toArray(selector),
    );
    gsap.from(targets, {
      y,
      duration: 0.84,
      ease: "power3.out",
      stagger: 0.055,
      scrollTrigger: {
        trigger,
        start: "top 83%",
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
  window.addEventListener("task05:ready", () => ScrollTrigger.refresh(), {
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
