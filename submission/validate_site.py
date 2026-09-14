"""Check local HTML, CSS and JavaScript dependencies without a browser."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
CSS_URL = re.compile(r"url\(\s*(?:\"([^\"]*)\"|'([^']*)'|([^)]*))\s*\)")
JS_IMPORT = re.compile(r"(?:\bfrom\s+|\bimport\s*\(\s*)['\"]([^'\"]+)['\"]")
JS_URL = re.compile(r"new\s+URL\(\s*['\"]([^'\"]+)['\"]\s*,\s*import\.meta\.url")


class Page(HTMLParser):
    def __init__(self, text: str) -> None:
        super().__init__()
        self.references: list[str] = []
        self.ids: set[str] = set()
        self.feed(text)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if attributes.get("id"):
            self.ids.add(str(attributes["id"]))
        for name in ("href", "src", "poster"):
            if attributes.get(name):
                self.references.append(str(attributes[name]))


def validate_site(root: Path = ROOT) -> tuple[int, list[str]]:
    """Return the reference count and broken local dependencies.

    External URLs are outside this offline check. Runtime fetches and interactive
    behaviour are covered by the task checks and a separate browser smoke test.
    """
    root = root.resolve()
    pages = {
        path: Page(path.read_text(encoding="utf-8"))
        for path in root.rglob("*.html")
        if not {"vendor", "node_modules", ".git", "release"}.intersection(path.relative_to(root).parts)
    }
    failures: list[str] = []
    checked = 0

    def check(source: Path, reference: str) -> None:
        nonlocal checked
        parsed = urlsplit(reference.strip())
        if parsed.scheme or parsed.netloc or not parsed.path:
            return
        path = unquote(parsed.path)
        target = (root / path.lstrip("/") if path.startswith("/") else source.parent / path).resolve()
        checked += 1
        if not target.is_relative_to(root) or not target.exists():
            failures.append(f"{source.relative_to(root)} -> {reference}")

    for path, page in pages.items():
        for reference in page.references:
            check(path, reference)
    for path in (root / "site").rglob("*.css"):
        for match in CSS_URL.finditer(path.read_text(encoding="utf-8")):
            check(path, next(value for value in match.groups() if value is not None))
    for path in (root / "site" / "assets").glob("*.js"):
        text = path.read_text(encoding="utf-8")
        for reference in JS_IMPORT.findall(text) + JS_URL.findall(text):
            check(path, reference)
    if not (root / "site/index.html").is_file():
        failures.append("missing site/index.html")
    return checked, sorted(set(failures))


def main() -> int:
    checked, failures = validate_site()
    print(f"Website dependencies: {'FAIL' if failures else 'PASS'} ({checked} local references)")
    for failure in failures:
        print(f"- {failure}")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
