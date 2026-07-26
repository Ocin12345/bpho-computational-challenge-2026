"""Static integrity checks for the self-contained Task 8 browser app."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


APP_DIRECTORY = Path(__file__).resolve().parent / "app"
REQUIRED_FILES = (
    "index.html",
    "styles.css",
    "physics.js",
    "statistics.js",
    "app.js",
    "package.json",
    "favicon.svg",
)
REQUIRED_IDS = {
    "theta-range",
    "theta-number",
    "phi-range",
    "phi-number",
    "classical-percent",
    "quantum-percent",
    "difference-value",
    "classical-substitution",
    "quantum-substitution",
    "reset-button",
    "live-results",
    "comparison-chart",
    "classical-curve",
    "quantum-curve",
    "chart-current-line",
    "classical-marker",
    "quantum-marker",
    "photon-count",
    "simulation-seed",
    "next-sample-button",
    "reset-simulation-button",
    "classical-sample-percent",
    "quantum-sample-percent",
    "observed-sample-difference",
    "simulation-live",
}


class AppHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.references: list[str] = []
        self.module_scripts = 0
        self.range_inputs = 0
        self.number_inputs = 0
        self.preset_buttons = 0
        self.photon_count_presets = 0
        self.html_language = ""
        self.label_targets: set[str] = set()
        self.input_accessible_names: dict[str, str] = {}
        self.svg_label_references: list[tuple[str, ...]] = []
        self.skip_targets: list[str] = []
        self.main_ids: list[str] = []
        self.live_statuses = 0
        self.keyboard_graph_regions = 0

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attributes = dict(attrs)
        if tag == "html":
            self.html_language = str(attributes.get("lang") or "")
        if attributes.get("id"):
            self.ids.append(str(attributes["id"]))
        for attribute in ("src", "href"):
            if attributes.get(attribute):
                self.references.append(str(attributes[attribute]))
        if tag == "script" and attributes.get("type") == "module":
            self.module_scripts += 1
        if tag == "input" and attributes.get("type") == "range":
            self.range_inputs += 1
        if tag == "input" and attributes.get("type") == "number":
            self.number_inputs += 1
        if tag == "input" and attributes.get("id"):
            self.input_accessible_names[str(attributes["id"])] = str(
                attributes.get("aria-label") or ""
            )
        if tag == "label" and attributes.get("for"):
            self.label_targets.add(str(attributes["for"]))
        if tag == "svg" and attributes.get("role") == "img":
            references = tuple(
                str(attributes.get("aria-labelledby") or "").split()
            )
            self.svg_label_references.append(references)
        if tag == "a" and "skip-link" in str(attributes.get("class") or "").split():
            self.skip_targets.append(str(attributes.get("href") or ""))
        if tag == "main" and attributes.get("id"):
            self.main_ids.append(str(attributes["id"]))
        if (
            attributes.get("role") == "status"
            and attributes.get("aria-live") == "polite"
            and attributes.get("aria-atomic") == "true"
        ):
            self.live_statuses += 1
        if (
            attributes.get("role") == "region"
            and attributes.get("aria-label")
            and attributes.get("tabindex") == "0"
        ):
            self.keyboard_graph_regions += 1
        if tag == "button" and attributes.get("data-preset"):
            self.preset_buttons += 1
        if tag == "button" and attributes.get("data-photon-pairs"):
            self.photon_count_presets += 1


def main() -> int:
    for filename in REQUIRED_FILES:
        path = APP_DIRECTORY / filename
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"missing or empty app file: {filename}")

    styles = (APP_DIRECTORY / "styles.css").read_text(encoding="utf-8")
    if 'font-family: "Times New Roman", Times, serif;' not in styles:
        raise ValueError("app must use Times New Roman as its root typeface")
    for forbidden_font in ("Inter", "Segoe UI", "Cambria", "DejaVu"):
        if forbidden_font in styles:
            raise ValueError(f"app contains a forbidden fallback font: {forbidden_font}")

    parser = AppHTMLParser()
    parser.feed((APP_DIRECTORY / "index.html").read_text(encoding="utf-8"))
    if len(parser.ids) != len(set(parser.ids)):
        raise ValueError("app HTML contains duplicate element IDs")
    missing_ids = REQUIRED_IDS - set(parser.ids)
    if missing_ids:
        raise ValueError(f"app HTML is missing required IDs: {sorted(missing_ids)}")
    if parser.module_scripts != 1:
        raise ValueError("app must load exactly one JavaScript module entry point")
    if parser.html_language != "en":
        raise ValueError("app root language must be English")
    if parser.range_inputs != 2 or parser.number_inputs != 4:
        raise ValueError(
            "app must contain two angle sliders, two angle numbers and two simulation numbers"
        )
    if parser.preset_buttons != 5:
        raise ValueError("app must contain five approved presets")
    if parser.photon_count_presets != 4:
        raise ValueError("app must contain four photon-count presets")
    for input_id, aria_label in parser.input_accessible_names.items():
        if input_id not in parser.label_targets and not aria_label.strip():
            raise ValueError(f"input lacks an accessible name: {input_id}")
    if len(parser.svg_label_references) != 3:
        raise ValueError("app must expose both detector dials and the graph as images")
    for references in parser.svg_label_references:
        if len(references) < 2 or not set(references).issubset(parser.ids):
            raise ValueError("each SVG image must reference an existing title and description")
    if parser.skip_targets != ["#calculator-main"] or parser.main_ids != [
        "calculator-main"
    ]:
        raise ValueError("app must contain one working skip link to its main landmark")
    if parser.live_statuses != 2:
        raise ValueError("app must contain separate polite theory and simulation statuses")
    if parser.keyboard_graph_regions != 1:
        raise ValueError("graph must be a named, keyboard-scrollable region")

    for reference in parser.references:
        parsed = urlparse(reference)
        if parsed.scheme or parsed.netloc:
            raise ValueError(f"external runtime reference is forbidden: {reference}")
        if reference.startswith("#"):
            continue
        target = (APP_DIRECTORY / parsed.path).resolve()
        if not target.is_file() or APP_DIRECTORY.resolve() not in target.parents:
            raise ValueError(f"broken or escaping app reference: {reference}")

    print(
        "Task 8 app validation: PASS "
        "(7 files, 2 synchronized angle controls, 5 angle presets, 4 photon-count "
        "presets, 3 described SVGs, accessible live graph and simulation, "
        "offline-only assets)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
