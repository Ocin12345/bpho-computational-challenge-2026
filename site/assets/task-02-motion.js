(() => {
  const root = document.documentElement;
  const reduceMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)",
  ).matches;
  const gsap = window.gsap;
  const ScrollTrigger = window.ScrollTrigger;

  if (reduceMotion || !gsap || !ScrollTrigger) {
    root.classList.add("motion-fallback", "motion-ready");
    root.dataset.motionStatus = reduceMotion ? "reduced" : "fallback";
    return;
  }

  gsap.registerPlugin(ScrollTrigger);
  root.classList.add("motion-enhanced");
  root.dataset.motionStatus = "initialising";

  const observatory = document.querySelector(".observatory");
  const parameterDrawer = document.querySelector("#parameter-drawer");
  const collisionVisual = document.querySelector(".collision-visual");
  const evidenceContent = document.querySelector("[data-evidence-content]");
  const actionTrajectory = document.querySelector(".action-trajectory");
  const cleanups = [];
  const observers = [];
  const animationContext = gsap.context(() => {
    const heroTargets = gsap.utils.toArray(
      ".hero-copy > p, .hero-copy > h1, .hero-copy > span",
    );
    const sidebarTargets = gsap.utils.toArray(
      ".parameter-drawer > header, .control-workflow li, " +
        ".preset-grid button, .parameter-fields label, " +
        ".display-options button, .result-actions button, " +
        ".drawer-actions, .drawer-note",
    );

    gsap.set(".task-header", { autoAlpha: 0, y: -18 });
    gsap.set("#brownian-canvas", { autoAlpha: 0, scale: 1.018 });
    gsap.set(heroTargets, { autoAlpha: 0, y: 34 });
    gsap.set(".model-status, .chamber-key, .scroll-cue", {
      autoAlpha: 0,
    });
    gsap.set(".instrument-dock", { autoAlpha: 0, y: 28 });

    if (window.matchMedia("(min-width: 1180px)").matches) {
      gsap.set(sidebarTargets, { autoAlpha: 0, x: 18 });
    }

    const intro = gsap.timeline({
      defaults: { ease: "power3.out" },
      onComplete: () => {
        root.classList.add("motion-ready");
        root.dataset.motionStatus = "active";
        ScrollTrigger.refresh();
      },
    });

    intro
      .to(".task-header", { autoAlpha: 1, y: 0, duration: 0.72 })
      .to(
        "#brownian-canvas",
        { autoAlpha: 1, scale: 1, duration: 1.35 },
        0.04,
      )
      .to(
        heroTargets,
        {
          autoAlpha: 1,
          y: 0,
          duration: 0.92,
          stagger: 0.105,
        },
        0.19,
      )
      .to(
        ".model-status, .chamber-key",
        { autoAlpha: 1, duration: 0.62, stagger: 0.08 },
        0.48,
      )
      .to(
        ".instrument-dock",
        { autoAlpha: 1, y: 0, duration: 0.85 },
        0.56,
      )
      .to(".scroll-cue", { autoAlpha: 1, duration: 0.6 }, 0.8);

    if (window.matchMedia("(min-width: 1180px)").matches) {
      intro.to(
        sidebarTargets,
        {
          autoAlpha: 1,
          x: 0,
          duration: 0.62,
          stagger: 0.034,
        },
        0.26,
      );
    }

    const reveal = (trigger, targets, options = {}) => {
      const elements = gsap.utils.toArray(targets);
      if (!trigger || !elements.length) return null;
      return gsap.from(elements, {
        y: options.y ?? 30,
        duration: options.duration ?? 0.82,
        stagger: options.stagger ?? 0.076,
        ease: "power3.out",
        clearProps: "transform",
        scrollTrigger: {
          trigger,
          start: options.start ?? "top 82%",
          once: true,
        },
      });
    };

    const methodSection = document.querySelector(".method-section");
    reveal(
      methodSection,
      ".section-introduction > p, .section-introduction > h2, " +
        ".section-introduction > span",
    );
    reveal(
      document.querySelector(".model-ledger"),
      ".model-ledger > div",
      { start: "top 88%", stagger: 0.055, y: 20 },
    );
    reveal(
      document.querySelector(".physics-ribbon"),
      ".physics-ribbon",
      { start: "top 92%", y: 18 },
    );

    const evidenceSection = document.querySelector(".evidence-section");
    reveal(
      evidenceSection,
      ".evidence-heading > div, .evidence-heading > span",
    );
    reveal(
      document.querySelector(".evidence-metrics"),
      ".evidence-metrics > article",
      { start: "top 88%", stagger: 0.06, y: 22 },
    );
    reveal(document.querySelector(".scope-note"), ".scope-note", {
      start: "top 92%",
      y: 18,
    });

    let cardsRevealed = false;
    const revealEvidenceCards = () => {
      if (cardsRevealed || !evidenceContent || evidenceContent.hidden) return;
      cardsRevealed = true;
      reveal(
        evidenceContent,
        evidenceContent.querySelectorAll(".chart-card"),
        { start: "top 88%", stagger: 0.1, y: 26 },
      );
      ScrollTrigger.refresh();
    };

    if (evidenceContent) {
      const contentObserver = new MutationObserver(revealEvidenceCards);
      contentObserver.observe(evidenceContent, {
        attributes: true,
        attributeFilter: ["hidden"],
      });
      observers.push(contentObserver);
      revealEvidenceCards();
    }

    reveal(
      document.querySelector(".task02-action"),
      ".task02-action__copy > p, .task02-action__copy > h2, " +
        ".task02-action__copy > span, .task02-action__links",
      { start: "top 78%", stagger: 0.09, y: 32 },
    );

    if (actionTrajectory instanceof SVGPathElement) {
      const length = actionTrajectory.getTotalLength();
      gsap.set(actionTrajectory, {
        strokeDasharray: length,
        strokeDashoffset: length,
      });
      gsap.to(actionTrajectory, {
        strokeDashoffset: 0,
        ease: "none",
        scrollTrigger: {
          trigger: ".task02-action",
          start: "top 78%",
          end: "bottom 58%",
          scrub: 0.65,
        },
      });
      gsap.from(".action-endpoint", {
        scale: 0.35,
        transformOrigin: "center",
        ease: "power3.out",
        scrollTrigger: {
          trigger: ".task02-action",
          start: "top 58%",
          end: "bottom 68%",
          scrub: 0.5,
        },
      });
    }

    const media = gsap.matchMedia();
    media.add("(min-width: 1180px)", () => {
      if (!collisionVisual) return;
      ScrollTrigger.create({
        trigger: ".collision-stage",
        start: "top 94px",
        end: "bottom bottom-=90",
        pin: collisionVisual,
        pinSpacing: false,
        anticipatePin: 1,
        invalidateOnRefresh: true,
      });
    });
    cleanups.push(() => media.revert());
  });

  if (collisionVisual) {
    const collisionObserver = new IntersectionObserver(
      ([entry]) => {
        collisionVisual.classList.toggle(
          "is-motion-active",
          entry.isIntersecting,
        );
      },
      { threshold: 0.28 },
    );
    collisionObserver.observe(collisionVisual);
    observers.push(collisionObserver);
  }

  const tactileSelector =
    ".dock-button, .parameter-trigger, .preset-grid button, " +
    ".display-options button, .result-actions button, " +
    ".drawer-actions > button, .figure-export, " +
    ".task02-action__links a";

  const handleTactileClick = (event) => {
    if (!(event.target instanceof Element)) return;
    const target = event.target.closest(tactileSelector);
    if (!target) return;
    gsap.fromTo(
      target,
      { scale: 0.965 },
      { scale: 1, duration: 0.46, ease: "elastic.out(1, 0.55)" },
    );
  };
  document.addEventListener("click", handleTactileClick);
  cleanups.push(() => document.removeEventListener("click", handleTactileClick));

  const openButton = document.querySelector("[data-parameters-open]");
  const handleDrawerOpen = () => {
    if (
      window.matchMedia("(min-width: 1180px)").matches ||
      !parameterDrawer
    ) {
      return;
    }
    window.setTimeout(() => {
      const drawerItems = parameterDrawer.querySelectorAll(
        ":scope > header, .control-workflow li, .preset-grid button, " +
          ".parameter-fields label, .display-options button, " +
          ".result-actions button, .drawer-actions, .drawer-note",
      );
      gsap.fromTo(
        drawerItems,
        { autoAlpha: 0, x: 16 },
        {
          autoAlpha: 1,
          x: 0,
          duration: 0.54,
          stagger: 0.028,
          ease: "power3.out",
          clearProps: "opacity,visibility,transform",
        },
      );
    }, 90);
  };
  openButton?.addEventListener("click", handleDrawerOpen);
  cleanups.push(() =>
    openButton?.removeEventListener("click", handleDrawerOpen),
  );

  const handleRunState = (event) => {
    if (!event.detail?.running) return;
    gsap
      .timeline()
      .to("#brownian-canvas", {
        scale: 1.0035,
        duration: 0.34,
        ease: "power2.out",
      })
      .to("#brownian-canvas", {
        scale: 1,
        duration: 0.72,
        ease: "power3.out",
      });
    gsap.fromTo(
      ".model-status",
      { x: -5 },
      { x: 0, duration: 0.68, ease: "elastic.out(1, 0.6)" },
    );
  };

  const handleStep = () => {
    gsap.fromTo(
      ".dock-metrics dd",
      { autoAlpha: 0.45, y: -5 },
      {
        autoAlpha: 1,
        y: 0,
        duration: 0.52,
        stagger: 0.045,
        ease: "power3.out",
      },
    );
  };

  window.addEventListener("task02:runstate", handleRunState);
  window.addEventListener("task02:step", handleStep);
  cleanups.push(() => {
    window.removeEventListener("task02:runstate", handleRunState);
    window.removeEventListener("task02:step", handleStep);
  });

  const cleanup = () => {
    observers.forEach((observer) => observer.disconnect());
    cleanups.forEach((dispose) => dispose());
    ScrollTrigger.getAll().forEach((trigger) => trigger.kill());
    animationContext.revert();
  };
  window.addEventListener("pagehide", cleanup, { once: true });

  if (!observatory) {
    root.classList.add("motion-ready");
    root.dataset.motionStatus = "active";
  }
})();
