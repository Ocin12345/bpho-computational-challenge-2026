"""Validate the saved advanced-extension evidence against fresh calculations."""

from __future__ import annotations

import json

from submission.generate_advanced_extensions import (
    DEFAULT_DATA_OUTPUT,
    DEFAULT_SITE_OUTPUT,
    build_payload,
)


def main() -> int:
    expected = build_payload()
    failures: list[str] = []
    for path in (DEFAULT_DATA_OUTPUT, DEFAULT_SITE_OUTPUT):
        if not path.is_file():
            failures.append(f"missing {path}")
            continue
        observed = json.loads(path.read_text(encoding="utf-8"))
        if observed != expected:
            failures.append(f"saved evidence differs from fresh calculation: {path}")
    if expected.get("accepted") is not True:
        failures.append("fresh advanced-extension checks did not all pass")
    if failures:
        print("Advanced extension validation: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(
        "Advanced extension validation: PASS\n"
        f"{expected['passed_check_count']}/{expected['check_count']} checks; "
        f"{expected['task_count']} tasks"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
