(() => {
  const root = document.documentElement;
  const stage = document.querySelector(".simulation-stage");
  const stepOutput = document.querySelector("[data-current-step]");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  function updateStageState() {
    if (!stage || !stepOutput) return;
    const currentStep = Number(
      stepOutput.textContent.split("/")[0].replaceAll(",", "").trim(),
    );
    stage.classList.toggle(
      "has-walk",
      Number.isFinite(currentStep) && currentStep > 0,
    );
  }

  updateStageState();
  const stepObserver =
    stepOutput && stage
      ? new MutationObserver(updateStageState)
      : null;
  stepObserver?.observe(stepOutput, {
    childList: true,
    characterData: true,
    subtree: true,
  });

  const gsap = window.gsap;
  const ScrollTrigger = window.ScrollTrigger;

  if (!gsap || !ScrollTrigger || reduceMotion.matches) {
    root.dataset.motionStatus = reduceMotion.matches ? "reduced" : "fallback";
    window.addEventListener(
      "pagehide",
      () => stepObserver?.disconnect(),
      { once: true },
    );
    return;
  }

  gsap.registerPlugin(ScrollTrigger);
  root.classList.add("motion-ready");
  root.dataset.motionStatus = "active";

  const entrance = gsap.timeline({
    defaults: { duration: 0.78, ease: "power3.out" },
  });

  entrance
    .from(".lab-header", { yPercent: -100, duration: 0.62 })
    .from(".simulation-workspace", { y: 34 }, "-=0.34")
    .from(
      [
        ".stage-preface > p",
        ".stage-preface h1",
        ".stage-preface > span",
        ".stage-preface ul",
      ],
      { y: 24, stagger: 0.075 },
      "-=0.48",
    )
    .from(
      [".simulation-controls .control", ".seed-control", ".control-actions"],
      { x: 22, stagger: 0.055 },
      "-=0.62",
    )
    .from(".live-results > div", { y: 16, stagger: 0.045 }, "-=0.52");

  const revealGroups = [
    {
      trigger: ".ensemble-introduction",
      targets: [".ensemble-introduction .section-kicker", ".ensemble-introduction h2"],
      y: 42,
    },
    {
      trigger: ".theory-panel",
      targets: [".theory-heading", ".theory-equations article", ".theory-distribution p"],
      y: 30,
    },
    {
      trigger: ".ensemble-laboratory",
      targets: [
        ".ensemble-toolbar > *",
        ".ensemble-figure",
        ".ensemble-results > div",
        ".ensemble-actions",
      ],
      y: 26,
    },
    {
      trigger: ".validation-introduction",
      targets: [".validation-introduction h2"],
      y: 42,
    },
    {
      trigger: ".validation-laboratory",
      targets: [
        ".validation-overview",
        ".validation-figure",
        ".validation-limitations",
        ".validation-lock",
      ],
      y: 28,
    },
  ];

  revealGroups.forEach(({ trigger, targets, y }) => {
    const elements = targets.flatMap((selector) => gsap.utils.toArray(selector));
    elements.forEach((element) => element.setAttribute("data-reveal", ""));
    gsap.from(elements, {
      y,
      duration: 0.82,
      ease: "power3.out",
      stagger: 0.065,
      scrollTrigger: {
        trigger,
        start: "top 84%",
        once: true,
      },
    });
  });

  const wideScreen = window.matchMedia("(min-width: 900px)");
  let pointerFrame = 0;

  function handlePointerMove(event) {
    if (!wideScreen.matches || !stage) return;
    cancelAnimationFrame(pointerFrame);
    pointerFrame = requestAnimationFrame(() => {
      const x = (event.clientX / window.innerWidth - 0.5) * 5;
      const y = (event.clientY / window.innerHeight - 0.5) * 4;
      gsap.to(".stage-preface", {
        x,
        y,
        duration: 0.7,
        ease: "power2.out",
        overwrite: "auto",
      });
    });
  }

  window.addEventListener("pointermove", handlePointerMove, { passive: true });

  function cleanup() {
    cancelAnimationFrame(pointerFrame);
    stepObserver?.disconnect();
    window.removeEventListener("pointermove", handlePointerMove);
    entrance.kill();
    ScrollTrigger.getAll().forEach((trigger) => trigger.kill());
    gsap.killTweensOf("*");
  }

  window.addEventListener("pagehide", cleanup, { once: true });
})();
