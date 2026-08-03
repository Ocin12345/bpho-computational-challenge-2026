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
    .from(".hero-copy > p", { y: 22 }, "-=0.26")
    .from(".hero-copy h1", { y: 42 }, "-=0.58")
    .from(".hero-copy > span", { y: 28 }, "-=0.62")
    .from(".detector-laboratory", { y: 36 }, "-=0.65")
    .from(".result-comparison > *", { x: 26, stagger: 0.06 }, "-=0.6");

  const groups = [
    [".model-section", [".model-section .section-introduction > *", ".equation-comparison article", ".reference-derivation"]],
    [".sweep-section", [".sweep-section .section-introduction > *", ".sweep-laboratory", ".sweep-anchors article"]],
    [".landscape-section", [".landscape-section .section-introduction > *", ".landscape-figure", ".landscape-reading"]],
    [".sampling-section", [".sampling-section .section-introduction > *", ".sampling-controls > *", ".sample-card", ".sampling-boundary"]],
    [".evidence-section", [".evidence-section .section-introduction > *", ".validation-ledger article", ".figure-pair figure", ".evidence-lock", ".evidence-downloads a", ".scope-boundary"]],
  ];

  groups.forEach(([trigger, selectors]) => {
    const targets = selectors.flatMap((selector) =>
      gsap.utils.toArray(selector),
    );
    gsap.from(targets, {
      y: 36,
      duration: 0.83,
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
      gsap.to(".hero-copy", {
        x: (event.clientX / window.innerWidth - 0.5) * 6,
        y: (event.clientY / window.innerHeight - 0.5) * 5,
        duration: 0.75,
        ease: "power2.out",
        overwrite: "auto",
      });
    });
  }

  window.addEventListener("pointermove", handlePointerMove, { passive: true });
  window.addEventListener("task08:ready", () => ScrollTrigger.refresh(), {
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
