(() => {
  "use strict";

  const root = document.documentElement;
  const hero = document.querySelector(".radiation-hero");
  const liveCanvas = document.querySelector("#planck-live-chart");
  const scan = document.querySelector(".spectrum-scan");
  const reducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)",
  ).matches;

  root.classList.add("motion-ready");

  const revealGroups = [
    [".section-introduction", "default"],
    [".equation-story", "scale"],
    [".quantity-identity", "default"],
    [".model-ledger", "default"],
    [".constants-marquee", "default"],
    [".einstein-equation", "default"],
    [".evidence-heading", "default"],
    [".evidence-metrics", "default"],
    [".validation-carousel", "scale"],
    [".evidence-grid", "scale"],
    [".benchmark-table-wrap", "default"],
    [".brief-coverage", "default"],
    [".scope-note", "default"],
    [".action-chapter__copy", "default"],
  ];

  const revealElements = revealGroups
    .map(([selector, type], index) => {
      const element = document.querySelector(selector);
      if (!element) return null;
      element.dataset.motionReveal = type;
      element.style.setProperty(
        "--reveal-delay",
        `${Math.min(index % 3, 2) * 35}ms`,
      );
      return element;
    })
    .filter(Boolean);

  const revealImmediately = () => {
    revealElements.forEach((element) => element.classList.add("is-visible"));
  };

  if (reducedMotion || !("IntersectionObserver" in window)) {
    revealImmediately();
  } else {
    const revealObserver = new IntersectionObserver(
      (entries, observer) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        });
      },
      {
        threshold: 0.12,
        rootMargin: "0px 0px -8% 0px",
      },
    );
    revealElements.forEach((element) => revealObserver.observe(element));
  }

  const showPage = () => {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => root.classList.add("is-page-ready"));
    });
  };
  if (document.fonts?.ready) {
    Promise.race([
      document.fonts.ready,
      new Promise((resolve) => window.setTimeout(resolve, 700)),
    ]).then(showPage);
  } else {
    showPage();
  }

  function updateScanDistance() {
    if (!liveCanvas || !scan) return;
    const compact = liveCanvas.clientWidth < 540;
    const left = compact ? 55 : 70;
    const distance = Math.max(120, liveCanvas.clientWidth - left - 16);
    scan.style.setProperty("--scan-distance", `${distance}px`);
  }
  updateScanDistance();

  if (
    hero &&
    !reducedMotion &&
    window.matchMedia("(pointer: fine)").matches
  ) {
    let pointerFrame = 0;
    let nextX = 0;
    let nextY = 0;

    const commitParallax = () => {
      pointerFrame = 0;
      hero.style.setProperty("--parallax-x", `${nextX.toFixed(2)}px`);
      hero.style.setProperty("--parallax-y", `${nextY.toFixed(2)}px`);
    };

    hero.addEventListener(
      "pointermove",
      (event) => {
        const rect = hero.getBoundingClientRect();
        const normalizedX = (event.clientX - rect.left) / rect.width - 0.5;
        const normalizedY = (event.clientY - rect.top) / rect.height - 0.5;
        nextX = normalizedX * 12;
        nextY = normalizedY * 9;
        if (!pointerFrame) pointerFrame = requestAnimationFrame(commitParallax);
      },
      { passive: true },
    );

    hero.addEventListener("pointerleave", () => {
      nextX = 0;
      nextY = 0;
      if (!pointerFrame) pointerFrame = requestAnimationFrame(commitParallax);
    });
  }

  document.addEventListener("visibilitychange", () => {
    root.classList.toggle("is-page-hidden", document.hidden);
  });
  window.addEventListener("resize", updateScanDistance, { passive: true });

  const verdictCarousel = document.querySelector(".validation-carousel");
  const verdictSlides = Array.from(
    document.querySelectorAll("[data-verdict-slide]"),
  );
  const verdictPrevious = document.querySelector("[data-verdict-previous]");
  const verdictNext = document.querySelector("[data-verdict-next]");
  const verdictStatus = document.querySelector("[data-verdict-status]");
  let verdictIndex = 0;
  let verdictTimer = 0;
  let verdictAnimating = false;

  const setVerdict = (nextIndex, direction = 1) => {
    if (!verdictSlides.length || verdictAnimating) return;
    const normalizedIndex =
      (nextIndex + verdictSlides.length) % verdictSlides.length;
    if (normalizedIndex === verdictIndex) return;

    const current = verdictSlides[verdictIndex];
    const next = verdictSlides[normalizedIndex];
    next.hidden = false;
    next.setAttribute("aria-hidden", "false");
    verdictAnimating = true;

    const finish = () => {
      current.hidden = true;
      current.classList.remove("is-active");
      current.setAttribute("aria-hidden", "true");
      next.classList.add("is-active");
      verdictIndex = normalizedIndex;
      verdictAnimating = false;
      if (verdictStatus) {
        verdictStatus.textContent = `${verdictIndex + 1} / ${verdictSlides.length}`;
      }
    };

    if (
      reducedMotion ||
      !window.gsap ||
      typeof window.gsap.timeline !== "function"
    ) {
      finish();
      return;
    }

    window.gsap
      .timeline({ onComplete: finish })
      .to(current, {
        y: -18 * direction,
        opacity: 0,
        duration: 0.28,
        ease: "power2.in",
      })
      .fromTo(
        next,
        { y: 22 * direction, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.46,
          ease: "power3.out",
          clearProps: "transform,opacity",
        },
        0.18,
      );
  };

  const stopVerdictTimer = () => {
    if (!verdictTimer) return;
    window.clearInterval(verdictTimer);
    verdictTimer = 0;
  };

  const startVerdictTimer = () => {
    if (reducedMotion || verdictSlides.length < 2 || verdictTimer) return;
    verdictTimer = window.setInterval(() => {
      if (!document.hidden) setVerdict(verdictIndex + 1, 1);
    }, 6500);
  };

  verdictSlides.forEach((slide, index) => {
    slide.setAttribute("aria-hidden", index === 0 ? "false" : "true");
  });
  verdictPrevious?.addEventListener("click", () =>
    setVerdict(verdictIndex - 1, -1),
  );
  verdictNext?.addEventListener("click", () =>
    setVerdict(verdictIndex + 1, 1),
  );
  verdictCarousel?.addEventListener("mouseenter", stopVerdictTimer);
  verdictCarousel?.addEventListener("mouseleave", startVerdictTimer);
  verdictCarousel?.addEventListener("focusin", stopVerdictTimer);
  verdictCarousel?.addEventListener("focusout", (event) => {
    if (!verdictCarousel.contains(event.relatedTarget)) startVerdictTimer();
  });
  startVerdictTimer();

  const setupGsapStory = () => {
    const gsap = window.gsap;
    const ScrollTrigger = window.ScrollTrigger;
    if (
      reducedMotion ||
      !gsap ||
      !ScrollTrigger ||
      typeof gsap.registerPlugin !== "function"
    ) {
      root.dataset.gsapStatus = reducedMotion ? "reduced" : "fallback";
      return;
    }

    gsap.registerPlugin(ScrollTrigger);
    root.dataset.gsapStatus = "active";

    const media = gsap.matchMedia();
    media.add("(min-width: 1200px)", () => {
      const layout = document.querySelector(".einstein-scroll-layout");
      const heading = document.querySelector(".einstein-heading");
      const content = document.querySelector(".einstein-scroll-content");
      if (!layout || !heading || !content) return undefined;

      const pin = ScrollTrigger.create({
        trigger: layout,
        start: "top top+=104",
        end: () =>
          `+=${Math.max(360, content.offsetHeight - heading.offsetHeight)}`,
        pin: heading,
        pinSpacing: false,
        anticipatePin: 1,
        invalidateOnRefresh: true,
      });

      return () => pin.kill();
    });

    [".spectral-anatomy", ".einstein-chart-card"].forEach((selector) => {
      const element = document.querySelector(selector);
      if (!element) return;

      gsap.fromTo(
        element,
        { scale: 0.92, opacity: 0.48 },
        {
          scale: 1,
          opacity: 1,
          ease: "none",
          scrollTrigger: {
            trigger: element,
            start: "top 90%",
            end: "center 52%",
            scrub: 0.65,
          },
        },
      );

      gsap.to(element, {
        scale: 0.975,
        opacity: 0.7,
        ease: "none",
        scrollTrigger: {
          trigger: element,
          start: "bottom 42%",
          end: "bottom top",
          scrub: 0.65,
        },
      });
    });

    window.addEventListener("load", () => ScrollTrigger.refresh(), {
      once: true,
    });
  };

  setupGsapStory();
})();
