#!/usr/bin/env python3
"""Which .py files are instruments rather than production code, in one place.

    python3 instruments.py            # the classification, and what each signal caught
    python3 instruments.py --diff     # versus the old prefix-only rule
    python3 instruments.py --md       # the inventory as a markdown table
    python3 instruments.py --write-md # regenerate the block in INSTRUMENTS.md

Read-only; changes nothing. That sentence is deliberate rather than decorative: it is the
DOCSTRING signal below, applied to this file, so this module appears in its own report
instead of being the one thing the classification cannot account for.

WHY THIS EXISTS

`audit_surface_area.py` and `audit_all_tables.py` both need to tell an instrument from the
system it measures. Both used to carry their own hand-maintained prefix tuple, and both went
stale the same way: `measure_` did not exist when the tuples were written, so on 2026-10-22
all six `measure_*` instruments were being counted as production code — dropped from the
audit denominator and scanned for hand-written numeric tables, which reported
`measure_h1_provenance.py`'s own `LADDER` as a table in the system under audit.

Adding `measure_` to both tuples fixed six files and left the mechanism. A prefix list is an
enumeration that rots silently, and it rots in the flattering direction: a missed instrument
inflates the apparent amount of unaudited code and deflates the count of audits.

THREE SIGNALS

    PREFIX     a known instrument prefix
    NAME       "audit" anywhere in the stem — catches the suffix spellings
               (source_audit.py, ticker_audit.py, universe_audit.py), which the prefix
               rule missed for as long as both scripts have existed
    DOCSTRING  "read-only" FOLLOWED BY A PERIOD in the module docstring

DOCSTRING is the signal that does not rot, because it is a claim about what the file does
rather than about what it is called, and it is already the house convention: nearly every
instrument in this repo opens with "Read-only. From pipeline/:". A new instrument written to
that convention is classified correctly with no edit here.

A file matching none of the three is production code. `validate_pipeline.py` is the known
borderline case — it validates data and is very likely read-only, but says so nowhere, so it
stays classified as code until someone decides deliberately. Run this file directly to see
every classification with the signal that produced it.
"""
import ast
import re
from pathlib import Path

PREFIXES = ("audit_", "probe_", "verify_", "count_", "check_", "sim_", "simulate_",
            "diff_", "measure_", "patch_")

# The tuple both audits carried before 2026-10-22, kept only so --diff can measure what
# changed. Not used for classification.
LEGACY_PREFIXES = ("audit_", "probe_", "verify_", "count_", "check_", "sim_", "diff_")


def docstring_of(path):
    """The module docstring, or "" for anything unreadable or unparseable."""
    try:
        return ast.get_docstring(ast.parse(Path(path).read_text())) or ""
    except (OSError, SyntaxError, ValueError, UnicodeDecodeError):
        return ""


# Documented exceptions, in the form source_rules.py uses for NOT_SOURCES: the rule, plus
# the cases it gets wrong, each with the reason beside it. Keep this list short — a long one
# means the rule is wrong rather than incomplete.
NOT_INSTRUMENTS = {
    "cleanup_audit.py":
        "WRITES. 'HI. Data Cleanup - fix domain collisions, dupes, and bad mappings.' "
        "Caught by NAME because 'audit' is in the stem. Treating it as an instrument would "
        "exclude it from the audit, so its own tables would stop being scanned.",
}


def signal(path):
    """Which signal marks this file as an instrument, or None for production code."""
    p = Path(path)
    if p.name in NOT_INSTRUMENTS:
        return None
    if p.name.startswith(PREFIXES):
        return "PREFIX"
    if "audit" in p.stem.lower():
        return "NAME"
    # The period is load-bearing. This repo always writes the claim about the script as a
    # terminated sentence - "Read-only. From pipeline/:", "Read-only. Changes nothing.",
    # "Ticker Universe Audit v2. Read-only." A bare substring test also matched
    # api_server.py, whose docstring says "- Read-only: no write endpoints exposed" - true
    # of the API's ENDPOINTS, not of the file. That classified the production REST API as an
    # audit and would have excluded it from audit_all_tables.py's table scan, which is the
    # flattering direction this module exists to close.
    if re.search(r"read-only\s*\.", docstring_of(p), re.I):
        return "DOCSTRING"
    return None


def is_instrument(path):
    """True when this file measures the system rather than being part of it."""
    return signal(path) is not None


def split(paths):
    """(instruments, code), preserving input order."""
    ins, code = [], []
    for p in paths:
        (ins if is_instrument(p) else code).append(p)
    return ins, code


def _main():
    import sys

    if "--md" in sys.argv:
        print(markdown_table())
        return
    if "--write-md" in sys.argv:
        changed, msg = write_md()
        print(("updated  " if changed else "unchanged  ") + msg)
        sys.exit(0 if changed or msg == "already current" else 1)

    here = Path(__file__).parent
    files = sorted(here.glob("*.py"))
    rows = [(p, signal(p)) for p in files]
    ins = [(p, s) for p, s in rows if s]
    code = [p for p, s in rows if not s]

    print(f"{len(files)} .py files in {here}/\n")
    print(f"   instruments {len(ins)}   production code {len(code)}\n")

    for want in ("PREFIX", "NAME", "DOCSTRING"):
        hit = [p for p, s in ins if s == want]
        print(f"   {want:10} {len(hit):>3}")
        if want != "PREFIX":
            for p in hit:
                d = docstring_of(p).splitlines()
                print(f"      {p.name:34} {(d[0] if d else '-')[:50]}")
    if NOT_INSTRUMENTS:
        print(f"   EXCEPTIONS  {len(NOT_INSTRUMENTS):>3}   held as production code despite "
              f"matching a signal")
        for name, why in sorted(NOT_INSTRUMENTS.items()):
            print(f"      {name:34} {why[:52]}")
    print()

    if "--diff" in sys.argv:
        legacy = {p for p in files if p.name.startswith(LEGACY_PREFIXES)}
        now = {p for p, s in ins}
        gained = sorted(now - legacy, key=lambda p: p.name)
        lost = sorted(legacy - now, key=lambda p: p.name)
        print(f"VERSUS THE OLD PREFIX-ONLY RULE\n")
        print(f"   newly classified as instruments: {len(gained)}")
        for p in gained:
            print(f"      {p.name:34} via {signal(p)}")
        print(f"\n   no longer instruments: {len(lost)}")
        for p in lost:
            print(f"      {p.name}")
        if not lost:
            print("      none — the new rule is a strict superset, so nothing that was")
            print("      counted as an audit stopped being one.")
        print()

    print("   Production code, for review — anything here that measures rather than runs")
    print("   is a misclassification worth fixing:\n")
    for p in code:
        d = docstring_of(p).splitlines()
        print(f"      {p.name:34} {(d[0] if d else '(no docstring)')[:54]}")
    print("\nNothing changed. Read-only.")

# ── the inventory, as markdown ───────────────────────────────────────────────
MD_BEGIN = "<!-- INSTRUMENTS:BEGIN generated by `python3 instruments.py --write-md` -->"
MD_END = "<!-- INSTRUMENTS:END -->"


def _first_line(path):
    d = docstring_of(path).strip().splitlines()
    return d[0].strip() if d else "(no docstring)"


def markdown_table(directory=None):
    """The instrument inventory as a markdown table. Generated, never hand-edited."""
    here = Path(directory or Path(__file__).parent)
    rows = [(p, signal(p)) for p in sorted(here.glob("*.py"))]
    ins = [(p, s) for p, s in rows if s]
    code = [p for p, s in rows if not s]

    out = [f"**{len(ins)} instruments, {len(code)} production modules** in `{here.name}/`, "
           f"classified by `instruments.py`.", ""]
    out += ["| instrument | signal | what it answers |", "|---|---|---|"]
    for p, s in ins:
        desc = _first_line(p).replace("|", "\\|")
        out.append(f"| `{p.name}` | {s} | {desc} |")
    out += ["",
            "`signal` is how `instruments.py` classified it: **PREFIX** a known filename "
            "prefix, **NAME** \"audit\" in the stem, **DOCSTRING** a `read-only.` claim in "
            "the module docstring. DOCSTRING is the one that does not rot, because it "
            "describes behaviour rather than naming."]
    if NOT_INSTRUMENTS:
        plural = "" if len(NOT_INSTRUMENTS) == 1 else "s"
        out += ["", f"**{len(NOT_INSTRUMENTS)} documented exception{plural}** — matched a "
                    "signal, held as production code:", ""]
        for name, why in sorted(NOT_INSTRUMENTS.items()):
            out.append(f"- `{name}` — {why}")
    return "\n".join(out)


def write_md(path=None):
    """Replace the generated block in INSTRUMENTS.md. Returns (changed, message)."""
    md = Path(path or Path(__file__).parent / "INSTRUMENTS.md")
    if not md.exists():
        return False, f"{md} does not exist"
    text = md.read_text()
    if text.count(MD_BEGIN) != 1 or text.count(MD_END) != 1:
        return False, (f"expected exactly one {MD_BEGIN!r} and one {MD_END!r}; "
                       f"found {text.count(MD_BEGIN)} and {text.count(MD_END)}")
    head, rest = text.split(MD_BEGIN, 1)
    _, tail = rest.split(MD_END, 1)
    new = head + MD_BEGIN + "\n\n" + markdown_table() + "\n\n" + MD_END + tail
    if new == text:
        return False, "already current"
    md.write_text(new)
    return True, f"{md} updated ({len(text)} -> {len(new)} chars)"


if __name__ == "__main__":
    _main()
