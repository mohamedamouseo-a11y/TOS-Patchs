#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path("/var/www/TOS")

EXPECTED = {
    # Phase 1/2/3 V2 state must remain exactly intact.
    "backend/src/routes/files.routes.js": "12684b4f617766736dcc298a4c371143c000fca9",
    "backend/src/routes/users.routes.js": "2d65febb608d33aac2077e86eb70198feaaf50f6",
    "backend/src/services/companyDepartments.service.js": "c6d0979f71564f84293a72b05c5f142775d13ce9",
    "frontend/src/App.jsx": "930f4da68dd9fcf021b967576e3edee2b1cbd630",
    "frontend/src/lib/api.js": "d5fa521cd22495237ab41e1ebb463485d587ef6d",
    "frontend/src/pages/TeamPage.jsx": "e9e098e3a2e7ac7070ed6c6d6d6c674573a9a222",
    # This route file was not touched by Phases 1-3 and must still match production HEAD.
    "backend/src/routes/userProfile.routes.js": "85cfc07ad7fe6142f580f6853600af5d4ea24282",
}


def git_blob(path: Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], cwd=ROOT, text=True).strip()


def replace_exact(text: str, old: str, new: str, label: str) -> str:
    actual = text.count(old)
    if actual != 1:
        raise RuntimeError(f"{label}: expected exactly 1 match, found {actual}")
    return text.replace(old, new, 1)


def build_change():
    for rel, expected in EXPECTED.items():
        actual = git_blob(ROOT / rel)
        if actual != expected:
            raise RuntimeError(f"BLOB_MISMATCH {rel}: expected={expected} actual={actual}")

    rel = "backend/src/routes/userProfile.routes.js"
    text = (ROOT / rel).read_text(encoding="utf-8")

    old = '''  if (!target.avatarFileId) {\n    if (target.avatarUrl) return res.redirect(target.avatarUrl);\n    throw new AppError("Avatar not found", 404);\n  }'''

    new = '''  if (!target.avatarFileId) {\n    const avatarUrl = String(target.avatarUrl || "").trim();\n    if (!avatarUrl) throw new AppError("Avatar not found", 404);\n\n    // Legacy profile images were stored inline as data:image/...;base64,... values.\n    // Redirecting to a data URI copies the entire image into the Location header,\n    // which can exceed Nginx upstream-header buffers and produce HTTP 502.\n    // Serve legacy inline avatars as binary instead.\n    const dataMatch = avatarUrl.match(/^data:image\\/(png|jpeg|jpg|webp);base64,(.+)$/is);\n    if (dataMatch) {\n      const subtype = dataMatch[1].toLowerCase() === "jpg" ? "jpeg" : dataMatch[1].toLowerCase();\n      const buffer = Buffer.from(dataMatch[2].replace(/\\s+/g, ""), "base64");\n      if (!buffer.length) throw new AppError("Avatar not found", 404);\n      res.setHeader("Content-Type", `image/${subtype}`);\n      res.setHeader("Content-Length", String(buffer.length));\n      res.setHeader("Cache-Control", "private, max-age=604800, immutable");\n      return res.send(buffer);\n    }\n\n    if (/^https:\\/\\/[^\\s]+$/i.test(avatarUrl)) {\n      res.setHeader("Cache-Control", "private, max-age=3600");\n      return res.redirect(302, avatarUrl);\n    }\n\n    throw new AppError("Avatar not found", 404);\n  }'''

    text = replace_exact(text, old, new, "userProfile.legacyAvatarRedirect")
    return rel, text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.check == args.apply:
        parser.error("use exactly one of --check or --apply")

    rel, content = build_change()
    print(f"PHASE3_1_TARGET={rel}")

    if args.check:
        print("PHASE3_1_PATCH_CHECK=PASS")
        return 0

    path = ROOT / rel
    tmp = path.with_name(path.name + ".phase3_1.tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)
    print(f"UPDATED {rel} blob={git_blob(path)}")
    print("PHASE3_1_PATCH_APPLIED=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"PHASE3_1_PATCH_ERROR={exc}", file=sys.stderr)
        raise SystemExit(1)
