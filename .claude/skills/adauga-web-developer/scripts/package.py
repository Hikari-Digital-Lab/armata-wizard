#!/usr/bin/env python3
"""Package a finished landing job into a downloadable .zip for the human.

After the web developer writes index.html into the job dir (which already contains the
artist's images), this script zips index.html + the image files (flat, side by side, so
the HTML's relative basenames resolve) into a .zip and prints a MEDIA:<zip> line. The CEO
posts that line in the General topic and the Hermes gateway attaches the zip as a document.

The job dir defaults to the most recent job_* under the CEO's cache/landing/ — so the CEO
doesn't have to remember the exact path. It can also be passed explicitly with --jobdir.

Idempotent: the zip is named deterministically per job (landing_<jobname>.zip). If it already
exists and is newer than index.html, it is reused (no duplicate zips). It is rebuilt only when
index.html changed since (e.g. after a revision round).

Usage:
  package.py                         # zip the latest landing job
  package.py --jobdir /abs/job_dir   # zip a specific job
  package.py --jobdir ... --out /abs/name.zip
"""
import argparse
import os
import pathlib
import zipfile

HERE = pathlib.Path(__file__).resolve().parent
PROFILE_DIR = HERE.parents[2]  # <profile>/skills/package-landing/scripts/package.py
HERMES_HOME = pathlib.Path(os.environ.get("HERMES_HOME") or PROFILE_DIR)
LANDING_ROOT = HERMES_HOME / "cache" / "landing"

EXCLUDE_NAMES = {"BRIEF.md"}  # build inputs, not part of the deliverable
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}


def _latest_jobdir():
    if not LANDING_ROOT.is_dir():
        return None
    jobs = [p for p in LANDING_ROOT.glob("job_*") if p.is_dir()]
    return max(jobs, key=lambda p: p.stat().st_mtime) if jobs else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobdir", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    jobdir = pathlib.Path(a.jobdir) if a.jobdir else _latest_jobdir()
    if not jobdir or not jobdir.is_dir():
        print("ERROR: no landing job dir found. Run the assign-to-<dev> skill first (it creates one).")
        return

    index = jobdir / "index.html"
    if not index.is_file():
        print(
            f"ERROR: {index} not found — the developer hasn't written the HTML yet. "
            "Wait for his HTML:<path> reply before packaging."
        )
        return

    members = []
    for p in sorted(jobdir.iterdir()):
        if not p.is_file() or p.name in EXCLUDE_NAMES:
            continue
        if p.name == "index.html" or p.suffix.lower() in IMAGE_EXTS:
            members.append(p)

    out = pathlib.Path(a.out) if a.out else (LANDING_ROOT / f"landing_{jobdir.name}.zip")
    out.parent.mkdir(parents=True, exist_ok=True)

    # Idempotent: reuse an up-to-date zip; rebuild only if index.html changed since.
    if out.is_file() and out.stat().st_mtime >= index.stat().st_mtime:
        imgs = [p.name for p in members if p.name != "index.html"]
        print(f"REUSED existing zip for this job ({len(members)} files: index.html + {len(imgs)} image(s)).")
        print(f"MEDIA:{out}")
        print("Post that MEDIA line in the General topic with a short proud message; then stop.")
        return

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in members:
            z.write(p, arcname=p.name)  # flat: index.html + images side by side

    imgs = [p.name for p in members if p.name != "index.html"]
    print(f"PACKAGED {len(members)} files (index.html + {len(imgs)} image(s): {', '.join(imgs)})")
    print(f"MEDIA:{out}")
    print("Post that MEDIA line in the General topic with a short proud message; then stop.")


if __name__ == "__main__":
    main()
