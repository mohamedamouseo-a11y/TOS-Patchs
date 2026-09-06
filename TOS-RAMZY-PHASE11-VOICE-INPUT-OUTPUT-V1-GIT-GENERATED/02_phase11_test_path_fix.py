#!/usr/bin/env python3
from pathlib import Path

path = Path('/var/www/TOS/backend/src/agency-operator/tests/ramzyVoicePhase11.static.test.js')
if not path.exists():
    raise SystemExit('PHASE11_TEST_PATH_FIX=TEST_NOT_FOUND')
text = path.read_text(encoding='utf-8')
old = '''const here = path.dirname(fileURLToPath(import.meta.url));\nconst root = path.resolve(here, "../..");\nconst read = (relative) => readFile(path.join(root, relative), "utf8");\n'''
new = '''const here = path.dirname(fileURLToPath(import.meta.url));\nconst backendSrc = path.resolve(here, "../..");\nconst repoRoot = path.resolve(backendSrc, "../..");\nconst readBackend = (relative) => readFile(path.join(backendSrc, relative), "utf8");\nconst readRepo = (relative) => readFile(path.join(repoRoot, relative), "utf8");\n'''
if new not in text:
    if old not in text:
        raise SystemExit('PHASE11_TEST_PATH_FIX=ROOT_ANCHOR_NOT_FOUND')
    text = text.replace(old, new, 1)
text = text.replace('await read("routes/agent.routes.js")', 'await readBackend("routes/agent.routes.js")')
text = text.replace('await read("../frontend/src/components/RamzyAssistant.jsx")', 'await readRepo("frontend/src/components/RamzyAssistant.jsx")')
text = text.replace('await read("../frontend/src/lib/api.js")', 'await readRepo("frontend/src/lib/api.js")')
if 'await read(' in text:
    raise SystemExit('PHASE11_TEST_PATH_FIX=STALE_READ_CALL_PRESENT')
path.write_text(text, encoding='utf-8')
print('PHASE11_TEST_PATH_FIX=PASS')
