(() => {
  const canvas = document.querySelector("#probability-background");
  const context = canvas.getContext("2d");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const coarsePointer = window.matchMedia("(pointer: coarse)");
  const pointer = { x: 0.5, y: 0.5, active: false };
  let width = 1;
  let height = 1;
  let pixelRatio = 1;
  let particles = [];
  let lastTime = performance.now();
  let animationFrame = 0;
  let running = true;

  function randomParticle(index) {
    return {
      x: Math.random() * width,
      y: Math.random() * height,
      previousX: 0,
      previousY: 0,
      age: Math.random() * 220,
      life: 160 + Math.random() * 260,
      speed: 0.24 + Math.random() * 0.72,
      tone: 0.52 + (index % 5) * 0.06 + Math.random() * 0.04,
    };
  }

  function resetParticle(particle, index) {
    const replacement = randomParticle(index);
    Object.assign(particle, replacement);
    particle.previousX = particle.x;
    particle.previousY = particle.y;
  }

  function resize() {
    width = window.innerWidth;
    height = window.innerHeight;
    pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(width * pixelRatio);
    canvas.height = Math.round(height * pixelRatio);
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
    context.fillStyle = "#111210";
    context.fillRect(0, 0, width, height);
    const count = coarsePointer.matches ? 150 : Math.min(420, Math.round(width * 0.29));
    particles = Array.from({ length: count }, (_, index) => randomParticle(index));
  }

  function flowAngle(x, y, time) {
    const nx = x / width;
    const ny = y / height;
    let angle =
      Math.sin(nx * 8.2 + time * 0.18) * 1.18 +
      Math.cos(ny * 7.1 - time * 0.14) * 1.02 +
      Math.sin((nx + ny) * 10.4 + time * 0.08) * 0.46;

    if (pointer.active) {
      const dx = x - pointer.x * width;
      const dy = y - pointer.y * height;
      const distance = Math.hypot(dx, dy);
      const influence = Math.exp(-(distance * distance) / 52000);
      angle += (Math.atan2(dy, dx) + Math.PI / 2) * influence * 0.72;
    }
    return angle;
  }

  function render(now) {
    const delta = Math.min((now - lastTime) / 16.667, 2.2);
    lastTime = now;
    const time = now * 0.001;

    context.globalCompositeOperation = "source-over";
    context.fillStyle = "rgba(17, 18, 16, 0.11)";
    context.fillRect(0, 0, width, height);
    context.lineCap = "round";

    particles.forEach((particle, index) => {
      particle.previousX = particle.x;
      particle.previousY = particle.y;
      const angle = flowAngle(particle.x, particle.y, time);
      const speed = particle.speed * delta;
      particle.x += Math.cos(angle) * speed;
      particle.y += Math.sin(angle) * speed;
      particle.age += delta;

      const fadeIn = Math.min(1, particle.age / 34);
      const fadeOut = Math.min(1, (particle.life - particle.age) / 48);
      const alpha = Math.max(0, Math.min(fadeIn, fadeOut)) * 0.22;
      context.strokeStyle =
        `rgba(164, 67, 47, ${alpha * particle.tone})`;
      context.lineWidth = particle.speed > 0.7 ? 1.05 : 0.72;
      context.beginPath();
      context.moveTo(particle.previousX, particle.previousY);
      context.lineTo(particle.x, particle.y);
      context.stroke();

      if (
        particle.age >= particle.life ||
        particle.x < -20 ||
        particle.x > width + 20 ||
        particle.y < -20 ||
        particle.y > height + 20
      ) {
        resetParticle(particle, index);
      }
    });

    context.globalCompositeOperation = "source-over";
    if (running && !reduceMotion.matches) {
      animationFrame = requestAnimationFrame(render);
    }
  }

  function handlePointerMove(event) {
    pointer.x = event.clientX / window.innerWidth;
    pointer.y = event.clientY / window.innerHeight;
    pointer.active = true;
  }

  function handlePointerLeave() {
    pointer.active = false;
  }

  function handleVisibility() {
    if (document.hidden) {
      cancelAnimationFrame(animationFrame);
      return;
    }
    lastTime = performance.now();
    if (running && !reduceMotion.matches) {
      animationFrame = requestAnimationFrame(render);
    }
  }

  function cleanup() {
    running = false;
    cancelAnimationFrame(animationFrame);
    window.removeEventListener("pointermove", handlePointerMove);
    document.removeEventListener("mouseleave", handlePointerLeave);
    window.removeEventListener("resize", resize);
    document.removeEventListener("visibilitychange", handleVisibility);
  }

  window.addEventListener("pointermove", handlePointerMove, { passive: true });
  document.addEventListener("mouseleave", handlePointerLeave);
  window.addEventListener("resize", resize);
  document.addEventListener("visibilitychange", handleVisibility);
  window.addEventListener("pagehide", cleanup, { once: true });

  resize();
  animationFrame = requestAnimationFrame(render);
})();
