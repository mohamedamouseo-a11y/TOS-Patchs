#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path("/var/www/TOS")
EXPECTED_HEAD = "293280da438adb8f8d9a8a821fe29e1deff41dd1"
TARGET = "backend/src/server.js"
EXPECTED_TARGET_BLOB = "6949e80bf73c1d2a4d6c488e6ff1a5ecd8e3d7ee"

EXPECTED_PRE_MODIFIED = {
    "backend/src/routes/files.routes.js",
    "backend/src/routes/tasks.routes.js",
    "backend/src/routes/userProfile.routes.js",
    "backend/src/routes/users.routes.js",
    "backend/src/services/companyDepartments.service.js",
    "backend/src/utils/sanitize.js",
    "frontend/src/App.jsx",
    "frontend/src/lib/api.js",
    "frontend/src/pages/MyTaskWorkspace.jsx",
    "frontend/src/pages/TeamPage.jsx",
}

EXPECTED_BLOBS = {
    "backend/src/routes/files.routes.js": "12684b4f617766736dcc298a4c371143c000fca9",
    "backend/src/routes/tasks.routes.js": "805d70cead79aa0d225f9ba7ce63fbcafdfc8a8e",
    "backend/src/routes/users.routes.js": "2d65febb608d33aac2077e86eb70198feaaf50f6",
    "backend/src/services/companyDepartments.service.js": "c6d0979f71564f84293a72b05c5f142775d13ce9",
    "frontend/src/App.jsx": "c10eee4a657f75c6a128b31157f80cb4c0336640",
    "frontend/src/lib/api.js": "d5fa521cd22495237ab41e1ebb463485d587ef6d",
    "frontend/src/pages/MyTaskWorkspace.jsx": "e8a770c87264173c2c2925722c6bf408353bdf84",
    "frontend/src/pages/TeamPage.jsx": "e9e098e3a2e7ac7070ed6c6d6d6c674573a9a222",
}

PROFILE_ROUTE = "backend/src/routes/userProfile.routes.js"
SANITIZE = "backend/src/utils/sanitize.js"

OLD_BLOCK = '''const server = http.createServer();
const io = new Server(server, {
  path: SOCKET_PATH,
  cors: {
    origin: buildSocketCorsOrigin(),
    credentials: true,
  },
  cookie: true,
});

const app = createApp(io);
server.removeAllListeners("request");
server.on("request", app);'''

NEW_BLOCK = '''const app = createApp();
const server = http.createServer(app);
const io = new Server(server, {
  path: SOCKET_PATH,
  cors: {
    origin: buildSocketCorsOrigin(),
    credentials: true,
  },
  cookie: true,
});
app.set("io", io);'''

def run(*args):
    return subprocess.check_output(list(args), cwd=ROOT, text=True).strip()

def git_blob(rel):
    return run("git", "hash-object", str(ROOT / rel))

def tracked_modified():
    output = run("git", "diff", "--name-only")
    return {line.strip() for line in output.splitlines() if line.strip()}

def staged_modified():
    output = run("git", "diff", "--cached", "--name-only")
    return {line.strip() for line in output.splitlines() if line.strip()}

def guard_state():
    head = run("git", "rev-parse", "HEAD")
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"HEAD_MISMATCH expected={EXPECTED_HEAD} actual={head}")

    modified = tracked_modified()
    if modified != EXPECTED_PRE_MODIFIED:
        raise RuntimeError(
            "MODIFIED_SET_MISMATCH expected="
            + ",".join(sorted(EXPECTED_PRE_MODIFIED))
            + " actual="
            + ",".join(sorted(modified))
        )

    staged = staged_modified()
    if staged:
        raise RuntimeError("STAGED_FILES_PRESENT=" + ",".join(sorted(staged)))

    for rel, expected in EXPECTED_BLOBS.items():
        actual = git_blob(rel)
        if actual != expected:
            raise RuntimeError(f"BLOB_MISMATCH {rel}: expected={expected} actual={actual}")

    target_actual = git_blob(TARGET)
    if target_actual != EXPECTED_TARGET_BLOB:
        raise RuntimeError(
            f"TARGET_NOT_PRISTINE {TARGET}: expected={EXPECTED_TARGET_BLOB} actual={target_actual}"
        )

    target_head = run("git", "rev-parse", f"HEAD:{TARGET}")
    if target_head != EXPECTED_TARGET_BLOB:
        raise RuntimeError(
            f"TARGET_HEAD_BLOB_MISMATCH expected={EXPECTED_TARGET_BLOB} actual={target_head}"
        )

    profile = (ROOT / PROFILE_ROUTE).read_text(encoding="utf-8")
    profile_markers = [
        'const dataMatch = avatarUrl.match(/^data:image\\/(png|jpeg|jpg|webp);base64,(.+)$/is);',
        'return res.send(buffer);',
        'return res.redirect(302, avatarUrl);',
    ]
    for marker in profile_markers:
        if marker not in profile:
            raise RuntimeError(f"PHASE3_1_MARKER_MISSING {marker}")
    if 'if (target.avatarUrl) return res.redirect(target.avatarUrl);' in profile:
        raise RuntimeError("PHASE3_1_LEGACY_REDIRECT_STILL_PRESENT")

    sanitize = (ROOT / SANITIZE).read_text(encoding="utf-8")
    sanitize_markers = [
        "function compactChatAvatarUrl(user) {",
        'if (!/^data:image\\//i.test(avatarUrl)) return avatarUrl;',
        'return `/api/users/${encodeURIComponent(user.id)}/avatar`;',
        "avatar: compactChatAvatarUrl(user),",
    ]
    for marker in sanitize_markers:
        if marker not in sanitize:
            raise RuntimeError(f"PHASE4_MARKER_MISSING {marker}")

def build_change():
    path = ROOT / TARGET
    text = path.read_text(encoding="utf-8")
    count = text.count(OLD_BLOCK)
    if count != 1:
        raise RuntimeError(f"SOCKET_SERVER_BLOCK_MATCH_COUNT expected=1 actual={count}")
    if 'server.removeAllListeners("request");' not in text:
        raise RuntimeError("EXPECTED_REQUEST_LISTENER_REMOVAL_NOT_FOUND")
    updated = text.replace(OLD_BLOCK, NEW_BLOCK, 1)
    if 'server.removeAllListeners("request");' in updated:
        raise RuntimeError("REQUEST_LISTENER_REMOVAL_STILL_PRESENT")
    if 'const server = http.createServer(app);' not in updated:
        raise RuntimeError("HTTP_SERVER_APP_ATTACHMENT_MISSING")
    if 'app.set("io", io);' not in updated:
        raise RuntimeError("APP_IO_BINDING_MISSING")
    return updated

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.check == args.apply:
        parser.error("use exactly one of --check or --apply")

    guard_state()
    content = build_change()

    print(f"PHASE7_TARGET={TARGET}")
    print(f"PHASE7_TARGET_BASELINE_BLOB={EXPECTED_TARGET_BLOB}")

    if args.check:
        print("PHASE7_PATCH_CHECK=PASS")
        return 0

    path = ROOT / TARGET
    tmp = path.with_name(path.name + ".phase7.tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)
    print(f"UPDATED {TARGET} blob={git_blob(TARGET)}")
    print("PHASE7_PATCH_APPLIED=PASS")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"PHASE7_PATCH_ERROR={exc}", file=sys.stderr)
        raise SystemExit(1)
