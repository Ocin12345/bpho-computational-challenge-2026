(() => {
  const renderer = window.katex;
  const equations = document.querySelectorAll("math[data-latex]");

  equations.forEach((fallback) => {
    const source = fallback.dataset.latex;
    if (!source) return;

    const display = document.createElement("div");
    display.className = "math-display";
    display.dataset.latex = source;
    fallback.replaceWith(display);

    if (!renderer) {
      display.classList.add("math-display--fallback");
      display.textContent = fallback.getAttribute("aria-label") || source;
      return;
    }

    try {
      renderer.render(source, display, {
        displayMode: true,
        output: "htmlAndMathml",
        strict: "warn",
        throwOnError: true,
        trust: false,
      });
    } catch (error) {
      display.classList.add("math-display--fallback");
      display.textContent = fallback.getAttribute("aria-label") || source;
      console.error("Task 2 equation could not be rendered", error);
    }
  });
})();
