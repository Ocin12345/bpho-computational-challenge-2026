import * as THREE from "../vendor/packages/three/three.module.min.js";

const body = document.body;
const canvas = document.querySelector("#quantum-field");
const loader = document.querySelector("[data-loader]");
const loaderNumber = document.querySelector("[data-loader-number]");
const loaderBar = document.querySelector("[data-loader-bar]");
const fieldToggle = document.querySelector("[data-field-toggle]");
const fieldLabel = document.querySelector("[data-field-label]");
const fieldState = document.querySelector("[data-field-state]");
const pointerValue = document.querySelector("[data-pointer-value]");
const phaseButton = document.querySelector("[data-phase-shift]");
const cursor = document.querySelector("[data-cursor]");
const heroTitle = document.querySelector(".hero__title");
const enterLink = document.querySelector(".enter-link");
const taskRows = [...document.querySelectorAll(".task-row")];
const pageTransition = document.querySelector("[data-page-transition]");
const transitionNumber = document.querySelector("[data-transition-number]");
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
const coarsePointer = window.matchMedia("(pointer: coarse)");

body.classList.add("is-loading");

const state = {
  fieldLive: !reduceMotion.matches,
  phase: 0,
  pointer: new THREE.Vector2(0.5, 0.5),
  pointerTarget: new THREE.Vector2(0.5, 0.5),
  scroll: 0,
  loaderProgress: 0,
};

let renderer;
let material;
let animationFrame;
let lastFrame = performance.now();

function webGLAvailable() {
  try {
    const testCanvas = document.createElement("canvas");
    return Boolean(
      window.WebGLRenderingContext &&
        (testCanvas.getContext("webgl") ||
          testCanvas.getContext("experimental-webgl")),
    );
  } catch {
    return false;
  }
}

const vertexShader = `
  varying vec2 vUv;

  void main() {
    vUv = uv;
    gl_Position = vec4(position, 1.0);
  }
`;

const fragmentShader = `
  precision highp float;

  uniform float uTime;
  uniform float uPhase;
  uniform float uScroll;
  uniform float uIntensity;
  uniform vec2 uResolution;
  uniform vec2 uPointer;

  varying vec2 vUv;

  #define PI 3.14159265359

  float hash21(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
  }

  float wavePacket(
    vec2 p,
    vec2 centre,
    float spread,
    float frequency,
    float speed,
    float phase
  ) {
    vec2 q = p - centre;
    float envelope = exp(-dot(q, q) / spread);
    float directional = q.x * frequency + sin(q.y * 1.7 + phase) * 1.6;
    return envelope * sin(directional - uTime * speed + phase + uPhase);
  }

  vec3 spectrum(float t) {
    vec3 a = vec3(0.46, 0.42, 0.52);
    vec3 b = vec3(0.48, 0.45, 0.42);
    vec3 c = vec3(1.00, 0.82, 0.68);
    vec3 d = vec3(0.02, 0.23, 0.57);
    return a + b * cos(6.28318 * (c * t + d));
  }

  void main() {
    float aspect = uResolution.x / max(uResolution.y, 1.0);
    vec2 p = vUv * 2.0 - 1.0;
    p.x *= aspect;

    vec2 mouse = uPointer * 2.0 - 1.0;
    mouse.x *= aspect;
    p += mouse * vec2(0.08, -0.035);
    p.y += uScroll * 0.15;

    float slowTime = uTime * 0.32;
    vec2 c1 = vec2(0.52 + sin(slowTime) * 0.13, 0.30 + cos(slowTime * 0.8) * 0.10);
    vec2 c2 = vec2(-0.36 + cos(slowTime * 0.7) * 0.12, -0.05 + sin(slowTime) * 0.09);
    vec2 c3 = vec2(0.08 + mouse.x * 0.17, -0.54 + mouse.y * 0.11);

    float psi = 0.0;
    psi += wavePacket(p, c1, 0.54, 12.0, 1.15, 0.0);
    psi += wavePacket(p.yx, c2.yx, 0.72, 10.0, -0.82, 1.6);
    psi += wavePacket(p, c3, 0.35, 16.0, 1.52, 3.3);

    float radial1 = length(p - c1);
    float radial2 = length(p - c2);
    float rings =
      sin(radial1 * 28.0 - uTime * 1.4 + uPhase) *
      exp(-radial1 * 1.9);
    rings +=
      sin(radial2 * 23.0 + uTime * 1.05 - uPhase * 0.7) *
      exp(-radial2 * 1.5);
    psi += rings * 0.42;

    float amplitude = abs(psi);
    float density = smoothstep(0.055, 0.92, amplitude);
    float contourBase = abs(fract(psi * 4.8 + radial1 * 1.9) - 0.5) * 2.0;
    float contours = pow(1.0 - contourBase, 9.0);

    float fineBase = abs(fract((psi + radial2) * 13.0) - 0.5) * 2.0;
    float fineLines = pow(1.0 - fineBase, 18.0) * smoothstep(0.03, 0.6, amplitude);

    float pointerDistance = length(p - mouse);
    float pointerHalo = exp(-pointerDistance * 3.2) * 0.32;

    vec3 deep = vec3(0.012, 0.015, 0.070);
    vec3 colour = deep;
    vec3 phaseColour = spectrum(0.53 + psi * 0.16 + radial1 * 0.08 + uPhase * 0.025);
    vec3 secondColour = spectrum(0.12 + radial2 * 0.10 - psi * 0.08);

    colour += phaseColour * density * 0.92;
    colour += secondColour * contours * 1.45;
    colour += vec3(0.25, 0.90, 1.0) * fineLines * 0.65;
    colour += phaseColour * pointerHalo;

    vec2 gridUv = p * vec2(8.0, 8.0);
    vec2 grid = abs(fract(gridUv) - 0.5) / fwidth(gridUv);
    float gridLine = 1.0 - min(min(grid.x, grid.y), 1.0);
    colour += vec3(0.11, 0.20, 0.36) * gridLine * 0.08;

    vec2 starCell = floor((p + 10.0) * 34.0);
    vec2 starLocal = fract((p + 10.0) * 34.0) - 0.5;
    float star = smoothstep(0.055, 0.0, length(starLocal));
    star *= step(0.975, hash21(starCell));
    colour += vec3(0.55, 0.83, 1.0) * star * (0.25 + density);

    float vignette = 1.0 - smoothstep(0.45, 1.55, length(p * vec2(0.72, 0.92)));
    colour *= 0.48 + vignette * 0.72;

    float scan = sin(vUv.y * uResolution.y * 0.65) * 0.018;
    colour += scan;
    colour = mix(vec3(dot(colour, vec3(0.299, 0.587, 0.114))), colour, uIntensity);

    gl_FragColor = vec4(colour, 1.0);
  }
`;

function createField() {
  if (!webGLAvailable()) {
    body.classList.add("no-webgl");
    fieldState.textContent = "Static fallback";
    return false;
  }

  try {
    const mobile = window.innerWidth < 760 || coarsePointer.matches;
    renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: false,
      alpha: false,
      powerPreference: "high-performance",
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, mobile ? 1 : 1.65));
    renderer.setSize(window.innerWidth, window.innerHeight, false);

    const scene = new THREE.Scene();
    const camera = new THREE.Camera();
    const geometry = new THREE.PlaneGeometry(2, 2);

    material = new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader,
      uniforms: {
        uTime: { value: 0 },
        uPhase: { value: 0 },
        uScroll: { value: 0 },
        uIntensity: { value: 1 },
        uResolution: {
          value: new THREE.Vector2(
            window.innerWidth * renderer.getPixelRatio(),
            window.innerHeight * renderer.getPixelRatio(),
          ),
        },
        uPointer: { value: state.pointer.clone() },
      },
    });

    scene.add(new THREE.Mesh(geometry, material));

    const render = (now) => {
      const delta = Math.min((now - lastFrame) / 1000, 0.05);
      lastFrame = now;

      state.pointer.lerp(state.pointerTarget, 1 - Math.pow(0.001, delta));
      material.uniforms.uPointer.value.copy(state.pointer);
      material.uniforms.uScroll.value +=
        (state.scroll - material.uniforms.uScroll.value) * 0.04;
      material.uniforms.uPhase.value +=
        (state.phase - material.uniforms.uPhase.value) * 0.035;

      if (state.fieldLive) {
        material.uniforms.uTime.value += delta;
      }

      renderer.render(scene, camera);
      animationFrame = requestAnimationFrame(render);
    };

    animationFrame = requestAnimationFrame(render);
    return true;
  } catch (error) {
    console.warn("WebGL field unavailable; using static fallback.", error);
    body.classList.add("no-webgl");
    fieldState.textContent = "Static fallback";
    return false;
  }
}

function resizeField() {
  if (!renderer || !material) return;
  const mobile = window.innerWidth < 760 || coarsePointer.matches;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, mobile ? 1 : 1.65));
  renderer.setSize(window.innerWidth, window.innerHeight, false);
  material.uniforms.uResolution.value.set(
    window.innerWidth * renderer.getPixelRatio(),
    window.innerHeight * renderer.getPixelRatio(),
  );
}

function completeLoader(fieldReady) {
  const start = performance.now();
  const duration = reduceMotion.matches ? 150 : 1150;

  const advance = (now) => {
    const elapsed = now - start;
    const raw = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - raw, 3);
    state.loaderProgress = Math.round(eased * 100);
    loaderNumber.textContent = String(state.loaderProgress).padStart(2, "0");
    loaderBar.style.transform = `translateX(${state.loaderProgress - 100}%)`;

    if (raw < 1) {
      requestAnimationFrame(advance);
      return;
    }

    window.setTimeout(
      () => {
        loader.classList.add("is-complete");
        body.classList.remove("is-loading");
        body.classList.add("page-ready");
        fieldState.textContent = fieldReady ? "Coherent" : "Static fallback";
      },
      reduceMotion.matches ? 0 : 170,
    );
  };

  requestAnimationFrame(advance);
}

function updatePointer(event) {
  state.pointerTarget.set(
    event.clientX / window.innerWidth,
    1 - event.clientY / window.innerHeight,
  );
  pointerValue.textContent = `${state.pointerTarget.x.toFixed(2)} / ${state.pointerTarget.y.toFixed(2)}`;

  if (heroTitle && window.scrollY < window.innerHeight) {
    const shiftX = (state.pointerTarget.x - 0.5) * 18;
    const shiftY = (0.5 - state.pointerTarget.y) * 12;
    heroTitle.style.setProperty("--hero-shift-x", `${shiftX}px`);
    heroTitle.style.setProperty("--hero-shift-y", `${shiftY}px`);
  }

  if (!coarsePointer.matches) {
    cursor.classList.add("is-visible");
    cursor.style.transform = `translate(${event.clientX}px, ${event.clientY}px) translate(-50%, -50%)`;
  }
}

function setFieldLive(isLive) {
  state.fieldLive = isLive;
  fieldToggle.setAttribute("aria-pressed", String(isLive));
  fieldLabel.textContent = isLive ? "Field live" : "Field paused";
  fieldState.textContent = isLive ? "Coherent" : "Frozen";
}

function bindInteractions() {
  window.addEventListener("pointermove", updatePointer, { passive: true });
  window.addEventListener("resize", resizeField, { passive: true });
  window.addEventListener(
    "scroll",
    () => {
      state.scroll = window.scrollY / Math.max(window.innerHeight, 1);
    },
    { passive: true },
  );

  fieldToggle.addEventListener("click", () => {
    setFieldLive(!state.fieldLive);
  });

  phaseButton.addEventListener("click", () => {
    state.phase += Math.PI * 0.5;
    if (!state.fieldLive) setFieldLive(true);
  });

  if (enterLink && !coarsePointer.matches) {
    enterLink.addEventListener("pointermove", (event) => {
      const rect = enterLink.getBoundingClientRect();
      const x = event.clientX - (rect.left + rect.width / 2);
      const y = event.clientY - (rect.top + rect.height / 2);
      enterLink.style.transform = `translate(${x * 0.12}px, ${y * 0.18}px)`;
    });
    enterLink.addEventListener("pointerleave", () => {
      enterLink.style.transform = "";
    });
  }

  const accents = [
    "#41ecff",
    "#ff4f91",
    "#ffb938",
    "#8b6cff",
    "#35e6a3",
    "#ff695e",
    "#56a4ff",
    "#e95dff",
    "#f9e95e",
    "#22d8ff",
  ];

  taskRows.forEach((row, position) => {
    row.style.setProperty("--row-accent", accents[position]);
    row.addEventListener("pointermove", (event) => {
      const rect = row.getBoundingClientRect();
      row.style.setProperty("--row-x", `${event.clientX - rect.left}px`);
    });
    row.addEventListener("pointerenter", () => {
      state.phase = position * 0.72;
    });
    row.addEventListener("click", (event) => {
      if (
        event.defaultPrevented ||
        event.button !== 0 ||
        event.metaKey ||
        event.ctrlKey ||
        event.shiftKey ||
        event.altKey
      ) {
        return;
      }
      event.preventDefault();
      const task = String(position + 1).padStart(2, "0");
      transitionNumber.textContent = task;
      pageTransition.style.setProperty("--transition-accent", accents[position]);
      pageTransition.classList.add("is-active");
      window.setTimeout(() => {
        window.location.href = row.href;
      }, reduceMotion.matches ? 0 : 570);
    });
  });

  document.addEventListener("pointerover", (event) => {
    cursor.classList.toggle("is-link", Boolean(event.target.closest("a, button")));
  });

  const navLinks = [...document.querySelectorAll(".site-nav a")];
  const sections = [...document.querySelectorAll("main > section[id]")];
  const observer = new IntersectionObserver(
    (entries) => {
      const visible = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (!visible) return;
      navLinks.forEach((link) => {
        link.classList.toggle(
          "is-active",
          link.getAttribute("href") === `#${visible.target.id}`,
        );
      });
    },
    { rootMargin: "-35% 0px -55% 0px", threshold: [0, 0.25, 0.5] },
  );
  sections.forEach((section) => observer.observe(section));
}

const fieldReady = createField();
bindInteractions();
setFieldLive(state.fieldLive);
completeLoader(fieldReady);
