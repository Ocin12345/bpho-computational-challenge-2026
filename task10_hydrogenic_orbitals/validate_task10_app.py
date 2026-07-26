"""Static, offline and accessibility-contract validation for the Task 10 app."""

from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable


APP_DIRECTORY = Path(__file__).resolve().parent / "app"
REQUIRED_FILES = (
    "index.html",
    "styles.css",
    "app.js",
    "physics.js",
    "favicon.svg",
    "package.json",
)
REQUIRED_IDS = {
    "explorer-main",
    "z-select",
    "n-select",
    "l-select",
    "m-select",
    "gallery-preset",
    "extent-range",
    "slice-range",
    "threshold-range",
    "opacity-range",
    "reset-all",
    "live-status",
    "glass-canvas",
    "glass-canvas-title",
    "glass-canvas-description",
    "orbit-left",
    "orbit-right",
    "zoom-out",
    "zoom-in",
    "reset-camera",
    "state-label",
    "energy-value",
    "bohr-value",
    "node-value",
    "slice-xy",
    "slice-xz",
    "slice-yz",
    "radial-chart",
    "radial-title",
    "radial-description",
}
RANGE_DOMAINS = {
    "extent-range": ("1.2", "6", "0.1"),
    "slice-range": ("7", "25", "2"),
    "threshold-range": ("0", "0.45", "0.01"),
    "opacity-range": ("0.2", "0.95", "0.01"),
}


@dataclass(frozen=True)
class AppCheck:
    """One explicit acceptance condition."""

    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class AppValidationReport:
    """Complete static-app acceptance report."""

    checks: tuple[AppCheck, ...]

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def failed_checks(self) -> tuple[AppCheck, ...]:
        return tuple(check for check in self.checks if not check.passed)


class _DocumentInventory(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list[tuple[str, dict[str, str]]] = []
        self.ids: list[str] = []
        self.canvas_fallbacks: list[str] = []
        self._canvas_text: list[str] | None = None

    def handle_starttag(
        self, tag: str, attributes: list[tuple[str, str | None]]
    ) -> None:
        attrs = {name: value or "" for name, value in attributes}
        self.elements.append((tag, attrs))
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        if tag == "canvas":
            self._canvas_text = []

    def handle_data(self, data: str) -> None:
        if self._canvas_text is not None:
            self._canvas_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "canvas" and self._canvas_text is not None:
            self.canvas_fallbacks.append("".join(self._canvas_text).strip())
            self._canvas_text = None

    def matching(self, tag: str | None = None, **attributes: str) -> list[dict[str, str]]:
        return [
            attrs
            for element_tag, attrs in self.elements
            if (tag is None or element_tag == tag)
            and all(attrs.get(name) == value for name, value in attributes.items())
        ]


def _check(name: str, condition: bool, detail: str) -> AppCheck:
    return AppCheck(name=name, passed=bool(condition), detail=detail)


def _local_references(inventory: _DocumentInventory) -> Iterable[str]:
    for tag, attrs in inventory.elements:
        attribute = "href" if tag in {"a", "link"} else "src" if tag == "script" else None
        if attribute and attrs.get(attribute):
            yield attrs[attribute]


def validate_app(app_directory: Path = APP_DIRECTORY) -> AppValidationReport:
    """Validate the app without network access or a browser runtime."""

    app_directory = Path(app_directory)
    missing_files = [name for name in REQUIRED_FILES if not (app_directory / name).is_file()]
    if missing_files or not (app_directory / "index.html").is_file():
        return AppValidationReport(
            (_check("required_files", False, f"missing: {', '.join(missing_files)}"),)
        )

    html = (app_directory / "index.html").read_text(encoding="utf-8")
    css = (app_directory / "styles.css").read_text(encoding="utf-8")
    javascript = "\n".join(
        (app_directory / name).read_text(encoding="utf-8")
        for name in ("app.js", "physics.js")
    )
    inventory = _DocumentInventory()
    inventory.feed(html)
    ids = set(inventory.ids)
    references = tuple(_local_references(inventory))
    local_references = tuple(
        reference
        for reference in references
        if not reference.startswith(("#", "data:", "mailto:", "tel:"))
        and not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", reference)
        and not reference.startswith("//")
    )
    unresolved = [
        reference
        for reference in local_references
        if not (app_directory / reference.split("#", 1)[0]).resolve().is_file()
    ]
    external_references = [
        reference
        for reference in references
        if reference.startswith("//")
        or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", reference)
    ]

    module_scripts = inventory.matching("script", type="module")
    imports = re.findall(r'from\s+["\']([^"\']+)["\']', javascript)
    bad_imports = [source for source in imports if not source.startswith("./")]
    unresolved_imports = [
        source for source in imports if not (app_directory / source).resolve().is_file()
    ]
    selects = inventory.matching("select")
    ranges = {
        attrs.get("id", ""): attrs
        for attrs in inventory.matching("input")
        if attrs.get("type") == "range"
    }
    range_domains = {
        control_id: (attrs.get("min"), attrs.get("max"), attrs.get("step"))
        for control_id, attrs in ranges.items()
    }
    canvases = inventory.matching("canvas")
    canvas_labels = [
        attrs.get("id", "unnamed")
        for attrs in canvases
        if attrs.get("role") != "img"
        or not (attrs.get("aria-label") or attrs.get("aria-labelledby"))
    ]
    radial_svgs = inventory.matching("svg", id="radial-chart", role="img")
    radial_labelled = bool(radial_svgs) and set(
        radial_svgs[0].get("aria-labelledby", "").split()
    ) == {"radial-title", "radial-description"}
    camera_ids = {
        attrs.get("id")
        for attrs in inventory.matching("button")
        if attrs.get("id") in {"orbit-left", "orbit-right", "zoom-out", "zoom-in", "reset-camera"}
    }
    labelled_by_missing = sorted(
        {
            token
            for _, attrs in inventory.elements
            for token in attrs.get("aria-labelledby", "").split()
            if token not in ids
        }
    )
    live_regions = inventory.matching(
        "p", role="status", **{"aria-live": "polite", "aria-atomic": "true"}
    )

    checks = (
        _check("required_files", not missing_files, f"{len(REQUIRED_FILES)} required files"),
        _check(
            "typography",
            'font-family: "Times New Roman", Times, serif;' in css
            and "Inter" not in css
            and "ui-sans-serif" not in javascript
            and "system-ui" not in javascript,
            "Times New Roman root and canvas typography",
        ),
        _check("unique_ids", len(inventory.ids) == len(ids), f"{len(ids)} unique element IDs"),
        _check("required_ids", REQUIRED_IDS.issubset(ids), f"missing: {sorted(REQUIRED_IDS - ids)}"),
        _check("local_references", not unresolved, f"unresolved: {unresolved}"),
        _check("offline_html", not external_references, f"external: {external_references}"),
        _check(
            "offline_javascript",
            not re.search(r"\b(fetch|XMLHttpRequest|WebSocket|EventSource)\s*\(", javascript),
            "no network API calls",
        ),
        _check(
            "module_graph",
            len(module_scripts) == 1 and not bad_imports and not unresolved_imports,
            f"imports={imports}; bad={bad_imports + unresolved_imports}",
        ),
        _check("state_controls", len(selects) == 5, "Z, n, l, m and official-gallery selectors"),
        _check("range_controls", range_domains == RANGE_DOMAINS, f"domains={range_domains}"),
        _check("accessible_canvases", len(canvases) == 4 and not canvas_labels, f"four labelled canvases; bad={canvas_labels}"),
        _check("canvas_fallbacks", len(inventory.canvas_fallbacks) == 4 and all(inventory.canvas_fallbacks), "meaningful fallback text on every canvas"),
        _check("accessible_radial_chart", radial_labelled, "radial SVG has title and dynamic description"),
        _check("keyboard_radial_region", len(inventory.matching("div", role="region", tabindex="0")) == 1, "one focusable scroll region"),
        _check("camera_controls", len(camera_ids) == 5, "orbit, zoom and reset controls"),
        _check("live_status", len(live_regions) == 1, "one polite atomic status"),
        _check(
            "skip_navigation",
            bool(inventory.matching("a", href="#explorer-main"))
            and bool(inventory.matching("main", id="explorer-main", tabindex="-1")),
            "skip link targets focusable main",
        ),
        _check("aria_references", not labelled_by_missing, f"missing: {labelled_by_missing}"),
        _check(
            "responsive_contract",
            "min-width: 320px" in css
            and "@media (max-width: 740px)" in css
            and "@media (max-width: 420px)" in css,
            "320 px floor and two mobile breakpoints",
        ),
        _check(
            "user_preferences",
            "@media (prefers-reduced-motion: reduce)" in css
            and "@media (forced-colors: active)" in css,
            "reduced-motion and forced-colour support",
        ),
        _check(
            "normalization_disclosure",
            "They never alter ∫|ψ|²dV=1" in html
            and "density is normalized before any display transform" in html,
            "physics and display transforms are separated",
        ),
        _check(
            "motion_disclosure",
            "stationary density · view rotation only" in html
            and "not electron motion" in javascript,
            "camera motion cannot be mistaken for electron motion",
        ),
        _check(
            "coordinate_and_scope_disclosure",
            "ϑ is polar colatitude and φ is azimuth" in html
            and "One non-relativistic electron in a point-Coulomb field" in html,
            "coordinate convention and model scope are explicit",
        ),
    )
    return AppValidationReport(checks)


def main() -> int:
    report = validate_app()
    passed = sum(check.passed for check in report.checks)
    print(f"Task 10 app validation: {passed}/{len(report.checks)} checks passed")
    for check in report.failed_checks:
        print(f"FAIL {check.name}: {check.detail}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
