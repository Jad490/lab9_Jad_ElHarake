"""Package verified deliverables and record file hashes for publication checks."""

import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]


def files():
    for path in sorted(ROOT.rglob("*")):
        relative = path.relative_to(ROOT)
        if not path.is_file():
            continue
        if any(part in (".git", ".venv", "__pycache__") for part in relative.parts):
            continue
        if path.name.startswith(".coverage") and path.name != ".coveragerc":
            continue
        if path.name in (".DS_Store", "manifest.json") or path.name.startswith("live_state") or path.suffix == ".pid" or "DRAFT" in path.name:
            continue
        # The instructor's original handout is retained locally as reference;
        # the submission archive contains the student's deliverables.
        if relative.as_posix() in ("reference/handout.docx", "reference/handout_extracted.txt"):
            continue
        yield path


def main():
    validation = json.loads((ROOT / "reports/validation.json").read_text())
    assert validation["status"] == "passed", "Validate the final report before packaging."
    assert validation["report_sha256"] == hashlib.sha256((ROOT / "lab9_Jad_ElHarake.docx").read_bytes()).hexdigest()
    manifest = []
    for path in files():
        data = path.read_bytes()
        manifest.append({
            "path": path.relative_to(ROOT).as_posix(), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "git_blob_sha": hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest(),
        })
    manifest_path = ROOT / "reports/manifest.json"
    manifest_path.write_text(json.dumps({"files": manifest}, indent=2))
    archive = ROOT.parent / "lab9_Jad_ElHarake_submission.zip"
    with ZipFile(archive, "w", compression=ZIP_DEFLATED) as z:
        for item in manifest:
            z.write(ROOT / item["path"], ROOT.name + "/" + item["path"])
        z.write(manifest_path, ROOT.name + "/reports/manifest.json")
        assert z.testzip() is None
    print(f"Packaged {len(manifest)+1} files: {archive}")
    print(f"Archive size: {archive.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
