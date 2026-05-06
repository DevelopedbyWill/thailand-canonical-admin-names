"""
End-to-end smoke test for the v1.0.0 build.

Snapshots the committed v1.0.0 data files, re-runs the orchestrator from cached
inputs, and diffs the regenerated outputs against the snapshot. Any byte-level
difference between snapshot and rebuild indicates non-determinism or drift in
the build pipeline and surfaces as a FAIL line in the smoke-test report.

The tabular files (CSV, Parquet) and the bundled GeoJSON polygons must
reproduce byte-identically. Verification reports and the build report carry
timestamps and are excluded from the diff.

Usage:
    python3 bin/smoke_test_v1_0_0.py

Reads:
    data/v1.0.0/thailand-adm{1,2,3}-...{csv,parquet}
    data/v1.0.0/thailand-adm{1,2,3}-polygons-v1.0.0.geojson

Writes:
    data/v1.0.0/smoke_test_report.md
"""

from __future__ import annotations

import datetime as dt
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "v1.0.0"
REPORT = DATA / "smoke_test_report.md"

# Canonical files that must reproduce byte-identically.
CANONICAL_FILES = [
    "thailand-adm1-provinces-v1.0.0.csv",
    "thailand-adm1-provinces-v1.0.0.parquet",
    "thailand-adm2-districts-v1.0.0.csv",
    "thailand-adm2-districts-v1.0.0.parquet",
    "thailand-adm3-subdistricts-v1.0.0.csv",
    "thailand-adm3-subdistricts-v1.0.0.parquet",
    "thailand-adm1-polygons-v1.0.0.geojson",
    "thailand-adm2-polygons-v1.0.0.geojson",
    "thailand-adm3-polygons-v1.0.0.geojson",
]


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    started = dt.datetime.utcnow()

    # Step 1: snapshot
    snapshot: dict[str, str | None] = {}
    sizes: dict[str, int] = {}
    print("snapshot existing v1.0.0 outputs")
    for name in CANONICAL_FILES:
        path = DATA / name
        snapshot[name] = sha256(path)
        sizes[name] = path.stat().st_size if path.exists() else 0
        print(f"  {name}: sha256={snapshot[name][:12] if snapshot[name] else 'missing'}, size={sizes[name]:,}")

    # Step 2: stash the canonical outputs to a temporary directory the
    # sandbox owns (filesystem ACLs may block delete inside the workspace
    # folder). We compare side-by-side after rebuild.
    stash = Path(tempfile.mkdtemp(prefix="tli_smoke_"))
    for name in CANONICAL_FILES:
        src = DATA / name
        if src.exists():
            shutil.copy2(src, stash / name)

    # Step 3: rebuild via the orchestrator. Skip network-dependent stages and
    # the methodology PDF compile (those are exercised separately).
    print("\nrebuild via orchestrator (--tables --skip-net)")
    cmd = [
        sys.executable,
        str(ROOT / "bin" / "build_v1_0_0.py"),
        "--tables",
        "--skip-net",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print("rebuild FAILED:")
        print(proc.stdout[-1500:])
        print(proc.stderr[-1500:])
        return 1
    print(proc.stdout.strip().splitlines()[-1] if proc.stdout else "")

    # Step 4: hash rebuilt outputs and compare
    print("\ndiff rebuilt vs snapshot")
    matches = []
    differs = []
    missing = []
    for name in CANONICAL_FILES:
        path = DATA / name
        rebuilt = sha256(path)
        snap = snapshot[name]
        if rebuilt is None:
            missing.append(name)
            print(f"  MISSING: {name}")
            continue
        if snap is None:
            # No prior snapshot — first build
            matches.append((name, rebuilt, "first build"))
            print(f"  NEW: {name}: sha256={rebuilt[:12]}")
            continue
        if rebuilt == snap:
            matches.append((name, rebuilt, "match"))
            print(f"  MATCH: {name}: sha256={rebuilt[:12]}")
        else:
            differs.append((name, snap, rebuilt))
            print(f"  DIFFER: {name}: snap={snap[:12]} rebuilt={rebuilt[:12]}")

    finished = dt.datetime.utcnow()

    # Build report
    lines = []
    lines.append("# v1.0.0 smoke-test report")
    lines.append("")
    lines.append(f"Run: {started.strftime('%Y-%m-%d %H:%M UTC')} → {finished.strftime('%H:%M UTC')}")
    lines.append(
        f"- Files checked: {len(CANONICAL_FILES)}"
    )
    lines.append(f"- Match: {len(matches)}")
    lines.append(f"- Differ: {len(differs)}")
    lines.append(f"- Missing after rebuild: {len(missing)}")
    lines.append("")
    lines.append("## File-by-file")
    lines.append("")
    lines.append("| Status | File | SHA-256 (snapshot) | SHA-256 (rebuilt) |")
    lines.append("|---|---|---|---|")
    for name in CANONICAL_FILES:
        snap = snapshot[name]
        rebuilt = sha256(DATA / name)
        snap_h = (snap or "")[:12] or "—"
        reb_h = (rebuilt or "")[:12] or "—"
        if rebuilt is None:
            status = "MISSING"
        elif snap is None:
            status = "NEW"
        elif rebuilt == snap:
            status = "MATCH"
        else:
            status = "DIFFER"
        lines.append(f"| {status} | `{name}` | `{snap_h}` | `{reb_h}` |")
    lines.append("")
    if differs:
        lines.append("## Investigation needed")
        lines.append("")
        lines.append(
            "The files above differ between snapshot and rebuild. The build "
            "pipeline reads cached inputs from `data/inputs/`, so a byte-level "
            "diff means either (a) a stage is not deterministic and writes "
            "non-canonical ordering or formatting, or (b) a stage was edited "
            "between the original v1.0.0 build and this smoke run. Inspect "
            "the diff with `diff <(python3 -c 'import csv, sys; ...') ...` "
            "or `parquet-tools` to identify the exact column."
        )
        lines.append("")

    # Restore the snapshot if the rebuild differed (so user is not stranded
    # with a non-canonical state). Otherwise leave the rebuilt files in place.
    if differs:
        print("\nrestoring snapshot (rebuild differed from canonical)")
        for name in CANONICAL_FILES:
            src = stash / name
            if src.exists():
                shutil.copy2(src, DATA / name)
    try:
        shutil.rmtree(stash)
    except (OSError, PermissionError) as exc:
        print(f"  stash cleanup skipped ({exc}) — manual rm /tmp/tli_smoke_*", file=sys.stderr)

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nreport: {REPORT}")
    print(
        f"summary: {len(matches)} match, {len(differs)} differ, {len(missing)} missing"
    )
    return 0 if not differs and not missing else 1


if __name__ == "__main__":
    sys.exit(main())
