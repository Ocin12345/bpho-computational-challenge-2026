"""Static, offline and accessibility-contract validation for the Task 9 app."""

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
    "cross-section.js",
    "favicon.svg",
    "package.json",
)
REQUIRED_IDS = {
    "explorer-main",
    "energy-range",
    "energy-number",
    "theta-range",
    "theta-number",
    "reset-button",
    "live-results",
    "collision-geometry",
    "fractional-shift",
    "electron-beta",
    "recoil-angle",
    "shift-chart",
    "beta-chart",
    "phi-chart",
    "differential-chart",
    "density-chart",
    "total-cross-section",
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

    def handle_starttag(
        self, tag: str, attributes: list[tuple[str, str | None]]
    ) -> None:
        attrs = {name: value or "" for name, value in attributes}
        self.elements.append((tag, attrs))
        if attrs.get("id"):
            self.ids.append(attrs["id"])

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
        for name in ("app.js", "physics.js", "cross-section.js")
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

    inputs = inventory.matching("input")
    ranges = [attrs for attrs in inputs if attrs.get("type") == "range"]
    numbers = [attrs for attrs in inputs if attrs.get("type") == "number"]
    energy_presets = [attrs for attrs in inventory.matching("button") if "data-energy" in attrs]
    angle_presets = [attrs for attrs in inventory.matching("button") if "data-theta" in attrs]
    svg_images = inventory.matching("svg", role="img")
    bad_svg_labels = [
        attrs.get("id", "unnamed")
        for attrs in svg_images
        if len(attrs.get("aria-labelledby", "").split()) != 2
        or not set(attrs.get("aria-labelledby", "").split()).issubset(ids)
    ]
    graph_regions = inventory.matching("div", role="region", tabindex="0")
    live_regions = inventory.matching("p", role="status", **{"aria-live": "polite"})
    module_scripts = inventory.matching("script", type="module")
    labelled_by_missing = sorted(
        {
            token
            for _, attrs in inventory.elements
            for token in attrs.get("aria-labelledby", "").split()
            if token not in ids
        }
    )
    imports = re.findall(r'from\s+["\']([^"\']+)["\']', javascript)
    bad_imports = [source for source in imports if not source.startswith("./")]
    unresolved_imports = [
        source for source in imports if not (app_directory / source).resolve().is_file()
    ]

    checks = (
        _check("required_files", not missing_files, f"{len(REQUIRED_FILES)} required files"),
        _check(
            "typography",
            'font-family: "Times New Roman", Times, serif;' in css
            and "Inter" not in css
            and 'font-family: Georgia' not in css,
            "strict Times New Roman root font with no sans-serif or Georgia override",
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
        _check("dual_controls", len(ranges) == 2 and len(numbers) == 2, "two range and two number controls"),
        _check(
            "control_domains",
            {(item.get("min"), item.get("max")) for item in ranges}
            == {("1", "5000"), ("0", "180")},
            "energy 1–5000 keV; angle 0–180 degrees",
        ),
        _check(
            "official_energy_presets",
            [attrs["data-energy"] for attrs in energy_presets]
            == ["50", "100", "200", "500", "1000"],
            "five official challenge energies",
        ),
        _check(
            "angle_presets",
            [attrs["data-theta"] for attrs in angle_presets]
            == ["0", "45", "90", "135", "180"],
            "five endpoint-aware angle presets",
        ),
        _check("accessible_svgs", len(svg_images) == 6 and not bad_svg_labels, f"six labelled SVGs; bad={bad_svg_labels}"),
        _check("keyboard_graph_regions", len(graph_regions) == 5, "five focusable scroll regions"),
        _check("live_results", len(live_regions) == 1, "one polite atomic result status"),
        _check(
            "skip_navigation",
            bool(inventory.matching("a", href="#explorer-main"))
            and bool(inventory.matching("main", id="explorer-main", tabindex="-1")),
            "skip link targets focusable main",
        ),
        _check("aria_references", not labelled_by_missing, f"missing: {labelled_by_missing}"),
        _check(
            "responsive_contract",
            "min-width: 320px" in css and "@media (max-width: 740px)" in css,
            "320 px floor and mobile breakpoint",
        ),
        _check(
            "user_preferences",
            "@media (prefers-reduced-motion: reduce)" in css
            and "@media (forced-colors: active)" in css,
            "reduced-motion and forced-colour support",
        ),
        _check(
            "extension_separation",
            "Klein–Nishina extension" in html
            and "official curves remain exact unweighted kinematics" in html.lower(),
            "optional angular weighting is visibly separated",
        ),
        _check(
            "endpoint_disclosure",
            "electron momentum is zero" in html and "continuous 90° limit" in html,
            "undefined zero-recoil direction disclosed",
        ),
    )
    return AppValidationReport(checks)


def main() -> int:
    report = validate_app()
    passed = sum(check.passed for check in report.checks)
    print(f"Task 9 app validation: {passed}/{len(report.checks)} checks passed")
    for check in report.failed_checks:
        print(f"FAIL {check.name}: {check.detail}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
