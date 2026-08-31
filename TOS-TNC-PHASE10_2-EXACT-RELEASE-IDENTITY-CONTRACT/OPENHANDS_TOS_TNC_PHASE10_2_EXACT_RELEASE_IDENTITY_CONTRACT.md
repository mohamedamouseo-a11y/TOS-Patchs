# TNC Phase 10.2 — Exact Release Identity Contract Correction

## Scope
Focused corrective patch for the failed Phase 10.1 implementation.

Phase 10.1 explicitly required the release manifest to preserve the exact asset path from `index.html`, including the `assets/` prefix. The implementation instead normalized both sides to basename and therefore violated the Phase 10.1 contract.

This patch fixes only that contract regression.

## Repository / baseline
- Repository: `mohamedamouseo-a11y/TOS`
- Branch: `main`
- Target server path: `/var/www/TOS`
- Expected remote `origin/main`: `28af5799c3bcba5cc9548ca68f16485ec7c803c6`
- Required parent of the current local HEAD: `61caeb3`
- The current local HEAD must be exactly one correction commit on top of `61caeb3`, created by the failed Phase 10.1 attempt.

Before implementation, verify:

```bash
CURRENT_HEAD=$(git rev-parse HEAD)
CURRENT_PARENT=$(git rev-parse HEAD^)
ORIGIN_MAIN=$(git rev-parse origin/main)
```

Required:
- `CURRENT_PARENT` resolves to commit `61caeb3`.
- `ORIGIN_MAIN` is exactly `28af5799c3bcba5cc9548ca68f16485ec7c803c6`.
- Working tree is clean.

If any condition fails, STOP and report the blocker.

## Confirmed regression
The failed Phase 10.1 implementation did the opposite of the specification:
- deploy manifest generation stores only the basename, e.g. `index-BAjH2dPf.js`
- preflight strips/normalizes the `assets/` prefix and compares basenames

This is NOT allowed.

The canonical contract is exact identity:

```text
release.mainJs === publishedIndexMainJs === publicIndexMainJs
```

where each value must be in this exact shape:

```text
assets/index-<real-hash>.js
```

No basename comparison, path stripping, prefix removal, or normalization workaround is allowed.

---

## Hard safety rules
- No reset.
- No rebase.
- No amend.
- No force push.
- No push.
- No Prisma changes.
- No migrations.
- No DB changes.
- No Auth/session changes.
- No scheduler/cron/worker changes.
- No Nginx configuration edits.
- Do not touch GitHub Sync UI.
- Do not redesign the Phase 10 Operations API/UI.
- Modify only the minimum release-generation/preflight code required by this regression.
- `tos-release.json` remains generated runtime output only and must not be tracked in Git.

---

## 10.2A — Restore exact manifest identity

Primary file:
- `scripts/tos-production-deploy.sh`

Required:
1. Read the actual built frontend `index.html`.
2. Extract the exact main JS path using the existing production HTML, in the form:

```text
assets/index-<real-hash>.js
```

3. Write that exact string into generated `tos-release.json.mainJs`.
4. Do not call `basename` on the extracted path.
5. Do not strip `assets/`.
6. Do not hardcode a hash or filename.
7. Preserve the existing real source SHA, UTC deploy/build timestamp, scope, and release schema/version metadata.
8. Publish `tos-release.json` with the same release as `index.html` and assets.

Acceptance:
- Published manifest `mainJs` starts with `assets/index-` and exactly equals the main JS path extracted from published `index.html`.

---

## 10.2B — Restore exact preflight comparison

Primary file:
- `scripts/tos-production-preflight.sh`

Required:
1. Remove the Phase 10.1 basename normalization/path-stripping workaround.
2. Compare exact strings only:
   - release manifest `mainJs`
   - canonical published `index.html` main JS path
   - public `index.html` main JS path
3. All three values must include `assets/` and be identical.
4. Build the public asset URL from that exact relative path and require HTTP 200.
5. Preserve all other Phase 10D checks unchanged.
6. Live preflight must fail on any identity mismatch.

Explicitly forbidden:
- `basename` comparison
- `.split('/').pop()` comparison
- regex/path normalization that removes `assets/`
- accepting `index-*.js` as equivalent to `assets/index-*.js`

Acceptance:

```text
release.mainJs == published main JS == public main JS
```

with exact string equality and all values containing `assets/`.

---

## 10.2C — Focused validation

Do not run the whole repository test suite.

Required sequence:
1. Inspect only the Phase 10.1 diff in `scripts/tos-production-deploy.sh` and `scripts/tos-production-preflight.sh`.
2. Apply the minimum correction.
3. Deploy frontend only through:

```bash
scripts/tos-production-deploy.sh --scope frontend
```

4. Run live preflight:

```bash
scripts/tos-production-preflight.sh --live
```

5. Capture literal production evidence:

```bash
cat /opt/apps/tamiyouz-front/build/tos-release.json

curl -fsS https://tos.tamiyouz.com/tos-release.json

curl -fsS https://tos.tamiyouz.com/ -o /tmp/tos-p10-2-public-index.html

grep -o 'assets/index-[^" ]*\.js' /opt/apps/tamiyouz-front/build/index.html

grep -o 'assets/index-[^" ]*\.js' /tmp/tos-p10-2-public-index.html

node - <<'NODE'
const fs = require('fs');
const release = JSON.parse(fs.readFileSync('/opt/apps/tamiyouz-front/build/tos-release.json','utf8'));
const published = fs.readFileSync('/opt/apps/tamiyouz-front/build/index.html','utf8').match(/assets\/index-[^" ]*\.js/)?.[0] || '';
const publicHtml = fs.readFileSync('/tmp/tos-p10-2-public-index.html','utf8');
const publicJs = publicHtml.match(/assets\/index-[^" ]*\.js/)?.[0] || '';
console.log(`RELEASE_MAIN_JS=${release.mainJs || ''}`);
console.log(`PUBLISHED_MAIN_JS=${published}`);
console.log(`PUBLIC_MAIN_JS=${publicJs}`);
console.log(`EXACT_MATCH=${Boolean(release.mainJs && release.mainJs === published && published === publicJs)}`);
console.log(`HAS_ASSETS_PREFIX=${String(release.mainJs || '').startsWith('assets/index-')}`);
process.exit(release.mainJs && release.mainJs === published && published === publicJs && release.mainJs.startsWith('assets/index-') ? 0 : 1);
NODE
printf 'IDENTITY_CHECK_EXIT=%s\n' "$?"

MAIN_JS=$(grep -o 'assets/index-[^" ]*\.js' /tmp/tos-p10-2-public-index.html | head -n1)
curl -sk -o /dev/null -w 'PUBLIC_MAIN_JS_HTTP=%{http_code}\n' "https://tos.tamiyouz.com/$MAIN_JS"

./scripts/tos-production-preflight.sh --live
printf 'PREFLIGHT_LIVE_EXIT=%s\n' "$?"
```

Required proof:
- `RELEASE_MAIN_JS` includes `assets/`
- `PUBLISHED_MAIN_JS` includes `assets/`
- `PUBLIC_MAIN_JS` includes `assets/`
- `EXACT_MATCH=true`
- `HAS_ASSETS_PREFIX=true`
- `IDENTITY_CHECK_EXIT=0`
- `PUBLIC_MAIN_JS_HTTP=200`
- `PREFLIGHT_LIVE_EXIT=0`

---

## Commit

After all checks pass, create exactly one NEW local commit on top of the failed Phase 10.1 commit:

```text
fix(tnc): enforce exact phase 10 release identity contract
```

DO NOT amend or rewrite the failed commit.
DO NOT PUSH.

---

## Evidence discipline

Return literal real values only.
Do not claim `PASS`, `SUCCESS`, or `verified` without the exact output that proves it.
Do not invent hashes, asset names, HTTP codes, or timestamps.
If any required proof cannot be obtained, set `BLOCKER` and stop.

## Final report format

Return exactly:

```text
BASE_HEAD=
BASE_PARENT=
ORIGIN_MAIN=
FILES_CHANGED=
RELEASE_MANIFEST_TRACKED=
PUBLISHED_RELEASE_JSON=
PUBLIC_RELEASE_JSON=
RELEASE_MAIN_JS=
PUBLISHED_MAIN_JS=
PUBLIC_MAIN_JS=
EXACT_MATCH=
HAS_ASSETS_PREFIX=
IDENTITY_CHECK_EXIT=
PUBLIC_MAIN_JS_HTTP=
PREFLIGHT_LIVE_EXIT=
COMMIT_SHA=
WORKTREE=
PUSH_PERFORMED=NO
BLOCKER=
```
