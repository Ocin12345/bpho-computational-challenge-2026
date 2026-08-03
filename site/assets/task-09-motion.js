(() => {
  const gsap = window.gsap;
  const ScrollTrigger = window.ScrollTrigger;
  if (!gsap || !ScrollTrigger) return;

  gsap.registerPlugin(ScrollTrigger);
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const animations = [];

  function reveal(targets, options = {}) {
    const elements = gsap.utils.toArray(targets);
    if (!elements.length) return;
    if (reduceMotion.matches) {
      gsap.set(elements, { clearProps: "all" });
      return;
    }
    const animation = gsap.fromTo(
      elements,
      { y: options.y ?? 34, opacity: 0 },
      {
        y: 0,
        opacity: 1,
        duration: options.duration ?? 0.9,
        stagger: options.stagger ?? 0.08,
        ease: "power3.out",
        scrollTrigger: {
          trigger: options.trigger || elements[0],
          start: options.start || "top 88%",
          once: true,
        },
      },
    );
    animations.push(animation);
  }

  if (!reduceMotion.matches) {
    animations.push(
      gsap.timeline().from(".hero-copy > p", {
        opacity: 0,
        y: 12,
        duration: 0.55,
      }).from(
        ".hero-copy h1",
        {
          opacity: 0,
          y: 36,
          duration: 1.05,
          ease: "power4.out",
        },
        "-=0.2",
      ).from(
        ".hero-copy > span",
        {
          opacity: 0,
          y: 22,
          duration: 0.75,
          ease: "power3.out",
        },
        "-=0.48",
      ),
    );
  }

  reveal(".collision-laboratory, .result-ledger", {
    trigger: ".collision-laboratory",
    stagger: 0.12,
  });
  reveal(".equation-grid article", {
    trigger: ".equation-grid",
    stagger: 0.07,
  });
  reveal(".endpoint-truth", { trigger: ".endpoint-truth" });
  reveal(".kinematics-laboratory", { trigger: ".kinematics-laboratory" });
  reveal(".anchor-strip article", {
    trigger: ".anchor-strip",
    stagger: 0.07,
  });
  reveal(".cross-section-figure, .cross-section-reading", {
    trigger: ".cross-section-layout",
    stagger: 0.09,
  });
  reveal(".validation-ledger article", {
    trigger: ".validation-ledger",
    stagger: 0.06,
  });
  reveal(".figure-pair figure", {
    trigger: ".figure-pair",
    stagger: 0.1,
  });

  function handlePreferenceChange() {
    if (!reduceMotion.matches) return;
    animations.forEach((animation) => {
      animation.scrollTrigger?.kill();
      animation.kill();
    });
    gsap.set(
      ".hero-copy > p, .hero-copy h1, .hero-copy > span, .collision-laboratory, .result-ledger, .equation-grid article, .endpoint-truth, .kinematics-laboratory, .anchor-strip article, .cross-section-figure, .cross-section-reading, .validation-ledger article, .figure-pair figure",
      { clearProps: "all" },
    );
  }

  reduceMotion.addEventListener?.("change", handlePreferenceChange);
  window.addEventListener("pagehide", () => {
    reduceMotion.removeEventListener?.("change", handlePreferenceChange);
    animations.forEach((animation) => {
      animation.scrollTrigger?.kill();
      animation.kill();
    });
    ScrollTrigger.getAll().forEach((trigger) => trigger.kill());
  });
})();
