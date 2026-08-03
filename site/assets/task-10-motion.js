(() => {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const motionImage = document.querySelector("[data-motion-image]");
  const motionCaption = document.querySelector("[data-motion-caption]");
  const animatedSource =
    "../../figures/task10/orbital_view_rotation.webp";
  const posterSource =
    "../../figures/task10/orbital_view_rotation_poster.png";

  function syncMotionAsset() {
    if (!motionImage || !motionCaption) return;
    motionImage.src = reduceMotion.matches ? posterSource : animatedSource;
    motionCaption.textContent = reduceMotion.matches
      ? "4K reduced-motion poster · stationary 3d density"
      : "4K WebP · 80 frames · 20 fps · exact 4-second loop";
  }

  syncMotionAsset();
  reduceMotion.addEventListener?.("change", syncMotionAsset);

  if (!reduceMotion.matches && window.gsap && window.ScrollTrigger) {
    window.gsap.registerPlugin(window.ScrollTrigger);
    const revealTargets = [
      ".section-introduction",
      ".equation-grid",
      ".normalization-boundary",
      ".structure-layout",
      ".node-ledger",
      ".family-ledger",
      ".gallery-figure",
      ".motion-figure",
      ".validation-ledger",
      ".figure-pair",
      ".evidence-lock",
      ".scope-boundary",
    ];
    revealTargets.forEach((selector) => {
      window.gsap.utils.toArray(selector).forEach((target) => {
        window.gsap.fromTo(
          target,
          { y: 20 },
          {
            y: 0,
            duration: 0.78,
            ease: "power3.out",
            scrollTrigger: {
              trigger: target,
              start: "top 88%",
              once: true,
            },
          },
        );
      });
    });
  }

  window.addEventListener(
    "pagehide",
    () => {
      reduceMotion.removeEventListener?.("change", syncMotionAsset);
      window.ScrollTrigger?.getAll().forEach((trigger) => trigger.kill());
    },
    { once: true },
  );
})();
