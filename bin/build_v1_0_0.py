"""
Top-level orchestrator for the v1.0.0 build.

Invokes the staged build scripts and validators in the order specified by the
methodology, then writes a build report. The script is the single reproducibility
entry point referenced inside `methodology/sections/08-capital-normalization.md`
and `methodology/sections/05-composition-pass.md`.

Stages (each is a separate script so individual passes remain editable):

    1. cross_check_inputs.py            — re-run cross-source spelling check
    2. build_v0_3_0.py                  — build the ADM1 base table (77×36)
    3. build_adm2_v1_0_0.py             — build the ADM2 districts table (928)
    4. build_adm3_v1_0_0.py             — build the ADM3 subdistricts table (7,436)
    5. validate_v1_0_0_full.py          — 49 cross-level integrity checks
    6. verify_enrichment.py             — 8 enrichment-spot-check suites
    7. verify_wikipedia_infobox_areas.py— Wikipedia area + centroid cross-check
    8. verify_alternates_wikipedia.py   — alternates Wikipedia attestation
    9. check_upstream_drift.py          — upstream cache freshness check
    10. test_v0_3_0.py                  — 54-case mutation test suite
    11. build_methodology.py            — compile methodology PDF and docx

Each stage prints its own log and exits non-zero on failure. The orchestrator
records pass/fail per stage in `data/v1.0.0/build_report.md`.

Usage:
    python3 bin/build_v1_0_0.py            # full pipeline
    python3 bin/build_v1_0_0.py --skip-net  # skip stages that hit Wikipedia / GitHub
    python3 bin/build_v1_0_0.py --tables    # rebuild ADM1/ADM2/ADM3 only
    python3 bin/build_v1_0_0.py --verify    # validators + verifications only
    python3 bin/build_v1_0_0.py --pdf       # methodology compile only
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin"
REPORT = ROOT / "data" / "v1.0.0" / "build_report.md"

# (id, label, script-path, hits-network)
STAGES: list[tuple[str, str, Path, bool]] = [
    ("cross",   "Cross-source spelling check",        BIN / "cross_check_inputs.py",          False),
    ("adm1",    "ADM1 build (77 provinces)",          BIN / "build_v0_3_0.py",                False),
    ("adm2",    "ADM2 build (928 districts)",         BIN / "build_adm2_v1_0_0.py",           False),
    ("adm3",    "ADM3 build (7,436 subdistricts)",    BIN / "build_adm3_v1_0_0.py",           False),
    ("validate","Cross-level validator",              BIN / "validate_v1_0_0_full.py",        False),
    ("enrich",  "Enrichment verification",            BIN / "verify_enrichment.py",           False),
    ("wp_area", "Wikipedia infobox cross-check",      BIN / "verify_wikipedia_infobox_areas.py", True),
    ("wp_alt",  "Alternates Wikipedia attestation",   BIN / "verify_alternates_wikipedia.py", True),
    ("drift",   "Upstream drift check",               BIN / "check_upstream_drift.py",        True),
    ("mutate",  "Mutation test suite",                BIN / "test_v0_3_0.py",                 False),
    ("pdf",     "Methodology compile",                BIN / "build_methodology.py",           False),
]

GROUPS = {
    "tables":  {"cross", "adm1", "adm2", "adm3"},
    "verify":  {"validate", "enrich", "wp_area", "wp_alt", "drift", "mutate"},
    "pdf":     {"pdf"},
}


def run_stage(stage_id: str, label: str, script: Path) -> tuple[bool, str]:
    """Run a single stage. Return (ok, tail-of-output)."""
    if not script.exists():
        return False, f"missing script: {script}"
    cmd = [sys.executable, str(script)]
    print(f"\n=== {label}  ({stage_id})")
    print(f"    {' '.join(cmd)}")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    tail = (proc.stdout or "")[-2000:] + (proc.stderr or "")[-500:]
    ok = proc.returncode == 0
    if not ok:
        print(f"    FAIL exit {proc.returncode}")
        print(tail.strip()[-1500:])
    else:
        # Surface the last informative line so humans can read progress fast.
        last = ""
        for line in reversed((proc.stdout or "").splitlines()):
            if line.strip():
                last = line.strip()
                break
        print(f"    ok | {last[:140]}")
    return ok, tail


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-net",
        action="store_true",
        help="skip stages that hit Wikipedia or GitHub",
    )
    parser.add_argument("--tables", action="store_true", help="rebuild tables only")
    parser.add_argument("--verify", action="store_true", help="validators only")
    parser.add_argument("--pdf", action="store_true", help="methodology compile only")
    args = parser.parse_args()

    selected: set[str] | None = None
    for flag, name in [(args.tables, "tables"), (args.verify, "verify"), (args.pdf, "pdf")]:
        if flag:
            selected = (selected or set()) | GROUPS[name]

    # Default: run everything
    chosen_stages = []
    for stage in STAGES:
        sid, label, script, hits_net = stage
        if selected is not None and sid not in selected:
            continue
        if args.skip_net and hits_net:
            print(f"skip (--skip-net): {label}")
            continue
        chosen_stages.append(stage)

    started = dt.datetime.utcnow()
    results: list[tuple[str, str, bool, str]] = []
    for sid, label, script, _net in chosen_stages:
        ok, tail = run_stage(sid, label, script)
        results.append((sid, label, ok, tail))

    # Build report
    finished = dt.datetime.utcnow()
    duration_s = (finished - started).total_seconds()
    failed = [r for r in results if not r[2]]

    lines = []
    lines.append("# v1.0.0 build report")
    lines.append("")
    lines.append(f"Run: {started.strftime('%Y-%m-%d %H:%M UTC')} → {finished.strftime('%H:%M UTC')} ({duration_s:.0f} s)")
    lines.append(f"Stages run: {len(results)}")
    lines.append(f"Stages failed: {len(failed)}")
    lines.append("")
    lines.append("| Stage | Status | Description |")
    lines.append("|---|---|---|")
    for sid, label, ok, _tail in results:
        status = "PASS" if ok else "FAIL"
        lines.append(f"| `{sid}` | {status} | {label} |")
    lines.append("")
    if failed:
        lines.append("## Failed-stage logs")
        lines.append("")
        for sid, label, _ok, tail in failed:
            lines.append(f"### {sid} — {label}")
            lines.append("")
            lines.append("```")
            lines.append(tail.strip())
            lines.append("```")
            lines.append("")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nreport: {REPORT}")
    print(f"summary: {len(results) - len(failed)}/{len(results)} stages passed")

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
