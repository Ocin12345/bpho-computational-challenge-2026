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
    .from(".hero-copy h1", { y: 38 }, "-=0.58")
    .from(".hero-copy > span", { y: 27 }, "-=0.61")
    .from(".task4-3d-embed", { y: 34 }, "-=0.7");

  const revealGroups = [
    {
      trigger: ".model-section",
      selectors: [
        ".model-section .section-introduction > *",
        ".equation-architecture article",
        ".domain-story > div",
        ".model-boundary",
      ],
      y: 34,
    },
    {
      trigger: ".comparison-section",
      selectors: [
        ".comparison-section .section-introduction > *",
        ".comparison-laboratory",
      ],
      y: 42,
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
  ];

  revealGroups.forEach(({ trigger, selectors, y }) => {
    const targets = selectors.flatMap((selector) =>
      gsap.utils.toArray(selector),
    );
    gsap.from(targets, {
      y,
      duration: 0.84,
      ease: "power3.out",
      stagger: 0.06,
      scrollTrigger: {
        trigger,
        start: "top 82%",
        once: true,
      },
    });
  });

  let pointerFrame = 0;

  function handlePointerMove(event) {
    if (window.innerWidth < 900) return;
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
  window.addEventListener("task04:ready", () => ScrollTrigger.refresh(), {
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
