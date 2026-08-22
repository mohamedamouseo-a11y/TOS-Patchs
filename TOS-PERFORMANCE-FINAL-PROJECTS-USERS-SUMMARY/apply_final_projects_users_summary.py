#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path('/var/www/TOS')
EXPECTED_HEAD = '293280da438adb8f8d9a8a821fe29e1deff41dd1'
TARGET = 'frontend/src/pages/ProjectsPage.jsx'
EXPECTED_TARGET_BLOB = '02ba1a49c282b940573c99302c7997cf906cbb5d'

EXPECTED_PRE_MODIFIED = {
    'backend/src/routes/files.routes.js',
    'backend/src/routes/tasks.routes.js',
    'backend/src/routes/userProfile.routes.js',
    'backend/src/routes/users.routes.js',
    'backend/src/server.js',
    'backend/src/services/companyDepartments.service.js',
    'backend/src/utils/sanitize.js',
    'frontend/src/App.jsx',
    'frontend/src/lib/api.js',
    'frontend/src/pages/MyTaskWorkspace.jsx',
    'frontend/src/pages/TeamPage.jsx',
}

EXPECTED_BLOBS = {
    'backend/src/routes/files.routes.js': '12684b4f617766736dcc298a4c371143c000fca9',
    'backend/src/routes/tasks.routes.js': '805d70cead79aa0d225f9ba7ce63fbcafdfc8a8e',
    'backend/src/routes/users.routes.js': '2d65febb608d33aac2077e86eb70198feaaf50f6',
    'backend/src/server.js': 'b54f8fe335214f21c9b6af17de3c697eb1c85370',
    'backend/src/services/companyDepartments.service.js': 'c6d0979f71564f84293a72b05c5f142775d13ce9',
    'frontend/src/App.jsx': 'c10eee4a657f75c6a128b31157f80cb4c0336640',
    'frontend/src/lib/api.js': 'd5fa521cd22495237ab41e1ebb463485d587ef6d',
    'frontend/src/pages/MyTaskWorkspace.jsx': 'e8a770c87264173c2c2925722c6bf408353bdf84',
    'frontend/src/pages/TeamPage.jsx': 'e9e098e3a2e7ac7070ed6c6d6d6c674573a9a222',
}

OLD_BLOCK = '''  useEffect(() => {\n    if (!allowedToCreate) return;\n    let ignore = false;\n    api.users.list()\n      .then((users) => { if (!ignore) setStaffUsers((users || []).filter((item) => item.status === "ACTIVE")); })\n      .catch(() => { if (!ignore) setStaffUsers([]); });\n    return () => { ignore = true; };\n  }, [allowedToCreate]);'''

NEW_BLOCK = '''  useEffect(() => {\n    if (!allowedToCreate) return;\n    let ignore = false;\n    api.users.list({ summary: true })\n      .then((users) => { if (!ignore) setStaffUsers((users || []).filter((item) => item.status === "ACTIVE")); })\n      .catch(() => { if (!ignore) setStaffUsers([]); });\n    return () => { ignore = true; };\n  }, [allowedToCreate]);'''


def run(*args):
    return subprocess.check_output(list(args), cwd=ROOT, text=True).strip()


def git_blob(rel):
    return run('git', 'hash-object', str(ROOT / rel))


def tracked_modified():
    out = run('git', 'diff', '--name-only')
    return {line.strip() for line in out.splitlines() if line.strip()}


def staged_modified():
    out = run('git', 'diff', '--cached', '--name-only')
    return {line.strip() for line in out.splitlines() if line.strip()}


def require_markers(rel, markers):
    text = (ROOT / rel).read_text(encoding='utf-8')
    for marker in markers:
        if marker not in text:
            raise RuntimeError(f'MARKER_MISSING {rel}: {marker}')


def guard_state():
    head = run('git', 'rev-parse', 'HEAD')
    if head != EXPECTED_HEAD:
        raise RuntimeError(f'HEAD_MISMATCH expected={EXPECTED_HEAD} actual={head}')

    modified = tracked_modified()
    if modified != EXPECTED_PRE_MODIFIED:
        raise RuntimeError(
            'MODIFIED_SET_MISMATCH expected=' + ','.join(sorted(EXPECTED_PRE_MODIFIED))
            + ' actual=' + ','.join(sorted(modified))
        )

    staged = staged_modified()
    if staged:
        raise RuntimeError('STAGED_FILES_PRESENT=' + ','.join(sorted(staged)))

    for rel, expected in EXPECTED_BLOBS.items():
        actual = git_blob(rel)
        if actual != expected:
            raise RuntimeError(f'BLOB_MISMATCH {rel}: expected={expected} actual={actual}')

    actual_target = git_blob(TARGET)
    if actual_target != EXPECTED_TARGET_BLOB:
        raise RuntimeError(f'TARGET_BLOB_MISMATCH {TARGET}: expected={EXPECTED_TARGET_BLOB} actual={actual_target}')
    head_target = run('git', 'rev-parse', f'HEAD:{TARGET}')
    if actual_target != head_target:
        raise RuntimeError(f'TARGET_NOT_PRISTINE {TARGET}: head={head_target} actual={actual_target}')

    require_markers('backend/src/routes/userProfile.routes.js', [
        'return res.send(buffer);',
        'return res.redirect(302, avatarUrl);',
    ])
    require_markers('backend/src/utils/sanitize.js', [
        'function compactChatAvatarUrl(user) {',
        'avatar: compactChatAvatarUrl(user),',
    ])
    require_markers('backend/src/routes/users.routes.js', [
        'const teamUserSummarySelect = {',
        'const summaryMode = req.query.summary === "1" || req.query.summary === "true";',
        'department: true,',
        'status: true,',
        'role: true,',
    ])
    require_markers('frontend/src/lib/api.js', [
        'list: (options = {}) => request(`/api/users${queryString({ summary: options.summary ? "1" : "" })}`)',
    ])
    require_markers('frontend/src/App.jsx', [
        'const ProjectsPage = lazy(',
        'const DesignQueuePage = lazy(',
        'const ChatPanel = lazy(',
    ])
    require_markers('backend/src/server.js', [
        'const app = createApp();',
        'const server = http.createServer(app);',
        'app.set("io", io);',
    ])
    server_text = (ROOT / 'backend/src/server.js').read_text(encoding='utf-8')
    if 'server.removeAllListeners("request")' in server_text:
        raise RuntimeError('PHASE7_LEGACY_REQUEST_LISTENER_REMOVAL_PRESENT')


def build_change():
    text = (ROOT / TARGET).read_text(encoding='utf-8')
    old_count = text.count(OLD_BLOCK)
    if old_count != 1:
        raise RuntimeError(f'PROJECTS_USERS_EFFECT_MATCH_COUNT expected=1 actual={old_count}')
    if 'api.users.list({ summary: true })' in text:
        raise RuntimeError('PROJECTS_USERS_SUMMARY_ALREADY_PRESENT')
    return text.replace(OLD_BLOCK, NEW_BLOCK, 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if args.check == args.apply:
        parser.error('use exactly one of --check or --apply')

    guard_state()
    new_text = build_change()

    print(f'FINAL_PATCH_TARGET={TARGET}')
    print('FINAL_PATCH_ACTION=api.users.list({ summary: true })')

    if args.check:
        print('FINAL_PROJECTS_USERS_PATCH_CHECK=PASS')
        return 0

    path = ROOT / TARGET
    tmp = path.with_name(path.name + '.final-users-summary.tmp')
    tmp.write_text(new_text, encoding='utf-8')
    os.replace(tmp, path)
    print(f'UPDATED {TARGET} blob={git_blob(TARGET)}')
    print('FINAL_PROJECTS_USERS_PATCH_APPLIED=PASS')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f'FINAL_PROJECTS_USERS_PATCH_ERROR={exc}', file=sys.stderr)
        raise SystemExit(1)
