"""
Resume Integrity Checker
Flags internal inconsistencies and unverifiable claims in a resume for a
human to verify. It does NOT accuse anyone of lying and does NOT score fit.

Design stance: verify, don't accuse. Every output is a neutral "item to
verify," because an LLM's judgment about truthfulness is probabilistic and
can be wrong or biased. A human makes every call.

This module separates the model call from the parsing/validation/formatting
so those can be tested deterministically. See tests/test_integrity.py.

Usage:
    python src/integrity_checker.py
"""

import os
import json
import csv
from pathlib import Path

from dotenv import load_dotenv
import anthropic

# Load the API key from the local .env file (never committed to GitHub)
load_dotenv()

# Check https://docs.claude.com for current model names
MODEL = "claude-sonnet-4-20250514"

# Severity levels a flag can carry. Ordered low -> high for sorting.
SEVERITY_ORDER = {"info": 0, "review": 1, "priority": 2}

# The shape every flag must have.
FLAG_SCHEMA = {
    "category": str,      # e.g. "timeline", "credential", "title"
    "severity": str,      # one of SEVERITY_ORDER
    "observation": str,   # what was noticed, stated neutrally
    "verify": str,        # the concrete thing a human should confirm
}

INTEGRITY_PROMPT = """You are an HR analyst preparing a verification checklist for a
recruiter. You review a resume for INTERNAL INCONSISTENCIES and claims that cannot be
confirmed from the resume itself.

You are NOT judging whether the candidate is honest. You do NOT accuse. You produce a
neutral list of items a human should verify during reference or background checks.

Look for things like:
- Timeline math that does not add up (e.g. total years of experience that exceed the
  span since graduation; overlapping full-time roles; gaps presented as employment)
- Credential or certification claims with no issuing body, date, or identifier
- Title or scope claims that are vague or unusually senior for the stated tenure
- Quantified achievements that are stated without any basis or unit

For each item, write a NEUTRAL observation and a concrete thing to verify. Never use
words like "fraud", "lie", "fake", or "suspicious". Frame everything as "confirm that..."

Resume:
{resume_text}

Respond with ONLY a JSON object, no other text:
{{
  "flags": [
    {{
      "category": "<timeline | credential | title | achievement | other>",
      "severity": "<info | review | priority>",
      "observation": "<neutral description of what was noticed>",
      "verify": "<the concrete thing a human should confirm>"
    }}
  ],
  "summary": "<one neutral sentence, e.g. 'N items flagged for verification'>"
}}

If nothing needs verifying, return an empty flags list and say so in the summary."""


# ---------------------------------------------------------------------------
# Pure functions (no network) -- what the test suite exercises.
# ---------------------------------------------------------------------------

def parse_report(raw: str) -> dict:
    """Turn the model's raw reply into a report dict, tolerating code fences."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1] if "\n" in cleaned else cleaned
        cleaned = cleaned.removeprefix("json").strip()
        cleaned = cleaned.removesuffix("```").strip()
    return json.loads(cleaned)


def validate_flag(flag: dict) -> list[str]:
    """Return a list of problems with a single flag. Empty means valid."""
    problems = []
    for field, expected_type in FLAG_SCHEMA.items():
        if field not in flag:
            problems.append(f"missing field: {field}")
        elif not isinstance(flag[field], expected_type):
            problems.append(f"{field} should be {expected_type.__name__}")
    if isinstance(flag.get("severity"), str) and flag["severity"] not in SEVERITY_ORDER:
        problems.append(f"unknown severity: {flag['severity']}")
    return problems


# Words this tool must never emit -- it verifies, it does not accuse.
ACCUSATORY_TERMS = {"fraud", "fraudulent", "lie", "lied", "lying", "fake", "faked",
                    "suspicious", "dishonest", "liar"}


def contains_accusatory_language(text: str) -> bool:
    """True if text uses accusatory words. Used to keep output neutral."""
    lowered = text.lower()
    return any(term in lowered.split() or term in lowered for term in ACCUSATORY_TERMS)


def sort_flags(flags: list[dict]) -> list[dict]:
    """Sort flags by severity, highest first (priority -> review -> info)."""
    return sorted(
        flags,
        key=lambda f: SEVERITY_ORDER.get(f.get("severity", "info"), 0),
        reverse=True,
    )


# ---------------------------------------------------------------------------
# Model call -- isolated so tests can swap in a fake client.
# ---------------------------------------------------------------------------

def check_resume(resume_text: str, client=None) -> dict:
    """Send one resume to Claude and return a parsed, neutral verification report."""
    if client is None:
        client = anthropic.Anthropic()

    response = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        messages=[{
            "role": "user",
            "content": INTEGRITY_PROMPT.format(resume_text=resume_text[:15000]),
        }],
    )
    report = parse_report(response.content[0].text)
    report["flags"] = sort_flags(report.get("flags", []))
    return report


def read_resume(path: Path) -> str:
    """Read a resume file (txt or pdf) into plain text."""
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return path.read_text(encoding="utf-8", errors="ignore")


def main():
    resumes_dir = Path("data/resumes")
    output_path = Path("verification_report.csv")

    if not resumes_dir.exists():
        print("Setup needed: create data/resumes/ and add resume files.")
        return

    rows = []
    for resume_file in sorted(resumes_dir.iterdir()):
        if resume_file.suffix.lower() not in {".txt", ".pdf"}:
            continue
        print(f"Reviewing {resume_file.name}...")
        try:
            report = check_resume(read_resume(resume_file))
            for flag in report["flags"]:
                rows.append({
                    "candidate": resume_file.stem,
                    "category": flag.get("category", ""),
                    "severity": flag.get("severity", ""),
                    "observation": flag.get("observation", ""),
                    "verify": flag.get("verify", ""),
                })
            if not report["flags"]:
                print("  No items flagged for verification.")
        except Exception as e:
            print(f"  Skipped ({e})")

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "candidate", "category", "severity", "observation", "verify",
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone. Verification checklist written to {output_path}")
    print("Reminder: these are items for a human to verify, not accusations.")


if __name__ == "__main__":
    main()
