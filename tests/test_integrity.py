"""
Evaluation suite for the Resume Integrity Checker.

Two layers, same as the resume screener:

  1. UNIT TESTS (deterministic, no API) -- parsing, validation, sorting, and the
     all-important neutrality guard that keeps accusatory words out of output.

  2. MODEL EVALS (live, gated) -- does the model actually behave neutrally and
     catch a planted inconsistency without inventing problems on a clean resume?

Run the free unit tests:
    python tests/test_integrity.py

Run everything, including live evals (needs ANTHROPIC_API_KEY):
    RUN_LIVE_EVALS=1 python tests/test_integrity.py

Also works with pytest:
    pytest tests/test_integrity.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from integrity_checker import (  # noqa: E402
    parse_report,
    validate_flag,
    sort_flags,
    contains_accusatory_language,
    check_resume,
)

RUN_LIVE = os.environ.get("RUN_LIVE_EVALS") == "1"


# ---- fake client so unit tests never hit the network -----------------------

class _FakeContent:
    def __init__(self, text): self.text = text

class _FakeResponse:
    def __init__(self, text): self.content = [_FakeContent(text)]

class FakeClient:
    def __init__(self, reply_text):
        self._reply = reply_text
        self.messages = self
    def create(self, **kwargs):
        return _FakeResponse(self._reply)


# ---- Layer 1: deterministic unit tests -------------------------------------

def test_parse_plain_json():
    report = parse_report('{"flags": [], "summary": "Nothing to verify"}')
    assert report["flags"] == []


def test_parse_tolerates_code_fences():
    raw = '```json\n{"flags": [], "summary": "ok"}\n```'
    assert parse_report(raw)["summary"] == "ok"


def test_validate_accepts_good_flag():
    flag = {
        "category": "timeline", "severity": "review",
        "observation": "Stated 10 years experience; graduation was 4 years ago.",
        "verify": "Confirm total years of professional experience.",
    }
    assert validate_flag(flag) == []


def test_validate_catches_missing_field():
    flag = {"category": "timeline", "severity": "review"}
    problems = validate_flag(flag)
    assert any("observation" in p for p in problems)


def test_validate_catches_unknown_severity():
    flag = {
        "category": "title", "severity": "EXTREME",
        "observation": "x", "verify": "y",
    }
    assert any("unknown severity" in p for p in validate_flag(flag))


def test_sorting_priority_first():
    flags = [
        {"severity": "info"}, {"severity": "priority"}, {"severity": "review"},
    ]
    order = [f["severity"] for f in sort_flags(flags)]
    assert order == ["priority", "review", "info"]


def test_neutrality_guard_flags_accusatory_words():
    """The guard must catch words this tool is forbidden from emitting."""
    assert contains_accusatory_language("This looks like fraud to me")
    assert contains_accusatory_language("The candidate lied about dates")


def test_neutrality_guard_passes_neutral_text():
    assert not contains_accusatory_language(
        "Confirm the total years of professional experience stated."
    )


def test_check_resume_sorts_output():
    """Even with a fake reply, the report's flags come back sorted by severity."""
    fake = FakeClient(
        '{"flags": ['
        '{"category":"a","severity":"info","observation":"o","verify":"v"},'
        '{"category":"b","severity":"priority","observation":"o","verify":"v"}'
        '], "summary": "2 items"}'
    )
    report = check_resume("resume text", client=fake)
    assert report["flags"][0]["severity"] == "priority"


# ---- Layer 2: live model evals (gated) -------------------------------------

# A resume with a planted, checkable inconsistency: graduated 2023 but claims
# "10+ years of experience" -- impossible, so a timeline flag is expected.
_INCONSISTENT_RESUME = """Jordan Blake
Senior Data Analyst

SUMMARY
10+ years of professional data analytics experience.

EXPERIENCE
Data Analyst, Acme Corp (2023 - present)

EDUCATION
B.S. Statistics, 2023
"""

# A clean resume with no internal contradictions -- expect few or no flags,
# and definitely no invented accusations.
_CLEAN_RESUME = """Riley Cooper
Operations Analyst

EXPERIENCE
Operations Analyst, Globex (2019 - present)
- Built reporting workflows in Python and SQL

EDUCATION
B.A. Economics, 2018
"""


def test_live_catches_planted_inconsistency():
    if not RUN_LIVE:
        print("  (skipped -- set RUN_LIVE_EVALS=1 to run)")
        return
    report = check_resume(_INCONSISTENT_RESUME)
    cats = [f.get("category") for f in report["flags"]]
    print(f"    flags: {cats}")
    assert any(c == "timeline" for c in report["flags"] and cats), \
        "Expected a timeline flag for the impossible experience span"


def test_live_output_is_neutral():
    """The headline eval: output must never contain accusatory language."""
    if not RUN_LIVE:
        print("  (skipped -- set RUN_LIVE_EVALS=1 to run)")
        return
    report = check_resume(_INCONSISTENT_RESUME)
    for flag in report["flags"]:
        blob = f"{flag.get('observation','')} {flag.get('verify','')}"
        assert not contains_accusatory_language(blob), \
            f"Accusatory language leaked into output: {blob}"
    print("    output neutral: OK")


def test_live_does_not_invent_on_clean_resume():
    if not RUN_LIVE:
        print("  (skipped -- set RUN_LIVE_EVALS=1 to run)")
        return
    report = check_resume(_CLEAN_RESUME)
    priority = [f for f in report["flags"] if f.get("severity") == "priority"]
    print(f"    clean resume flags: {len(report['flags'])} "
          f"({len(priority)} priority)")
    assert len(priority) == 0, "Invented a priority flag on a clean resume"


# ---- standalone runner -----------------------------------------------------

def _run():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    print("=" * 60)
    print("Resume Integrity Checker -- evaluation suite")
    print(f"Live model evals: {'ON' if RUN_LIVE else 'OFF (unit tests only)'}")
    print("=" * 60)
    for test in tests:
        try:
            test()
            print(f"PASS  {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL  {test.__name__}\n      {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR {test.__name__}\n      {type(e).__name__}: {e}")
            failed += 1
    print("=" * 60)
    print(f"{passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(_run())
