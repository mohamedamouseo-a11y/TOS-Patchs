# TNC Phase 10.1 — Release Identity Correction

## Scope
Focused correction for the Phase 10 production release identity mismatch discovered during live preflight verification.

This is **not** a new feature phase and must not expand Phase 10 scope.

## Repository / baseline
- Repository: `mohamedamouseo-a11y/TOS`
- Branch: `main`
- Target server path: `/var/www/TOS`
- Required local HEAD short SHA before implementation: `61caeb3`
- Expected remote `origin/main`: `28af5799c3bcba5cc9548ca68f16485ec7c803c6`
- Phase 10 initial commit already present locally: `03015a9`
- Phase 10 correction commit already present locally: `61caeb3`

## Confirmed defect
Live Phase 10 preflight is failing because release identity is represented inconsistently:

Production `index.html` references:

```text
assets/index-BAjH2dPf.js
```

while generated `tos-release.json` stores:

```text
index-BAjH2dPf.js
```

The manifest must contain the **exact asset path referenced by the built/published `index.html`**, including the `assets/` prefix.

The correct contract is:

```text
release.mainJs === publishedIndexMainJs === publicIndexMainJs
```

No path-stripping workaround is allowed in preflight.

---

## Hard safety rules
- STOP if `git rev-parse --short=7 HEAD` is not exactly `61caeb3`.
- STOP if `origin/main` is not exactly `28af5799c3bcba5cc9548ca68f16485ec7c803c6`.
- STOP if the working tree is dirty before implementation.
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
- Do not redesign Phase 10 backend APIs or Operations UI.
- Modify only the minimum release-generation/preflight code required by this defect.

---

## 10.1A — Correct release manifest generation

Primary expected file:
- `scripts/tos-production-deploy.sh`

Required behavior:
1. Read the actual built frontend `index.html` produced by the current frontend build.
2. Extract the exact hashed main JS path in this shape:

```text
assets/index-<real-hash>.js
```

3. Write that exact string to the generated public release manifest field:

```json
{
  "mainJs": "assets/index-<real-hash>.js"
}
```

4. Do not strip `assets/`.
5. Do not hardcode any JS hash or filename.
6. Preserve real `sourceSha`, timestamp, scope, and release schema/version metadata.
7. `tos-release.json` remains generated runtime output only and must not become tracked source.
8. The generated manifest must be published together with the same `index.html`/assets release under the canonical publish directory.

Acceptance:
- Published `tos-release.json.mainJs` exactly matches the string extracted from published `index.html`.

---

## 10.1B — Keep preflight comparison exact

Primary expected file only if correction is required:
- `scripts/tos-production-preflight.sh`

Required:
- Do **not** fix the issue by normalizing away `assets/`.
- Do **not** compare basenames only.
- Compare the exact strings:
  - `release.mainJs`
  - published `index.html` main JS path
  - public `index.html` main JS path
- All three must be identical.
- The exact public asset URL must return HTTP 200.
- Existing Phase 10D checks must remain intact.

Acceptance:

```text
release.mainJs == published main JS == public main JS
```

and live preflight exits `0` only when all Phase 10D checks pass.

---

## 10.1C — Focused validation

Do not run the full repository test suite.

Required sequence:
1. Inspect current release-generation code and current Phase 10D comparison only.
2. Make the minimum correction.
3. Run one frontend build only if needed by the canonical deploy flow.
4. Deploy frontend only through:

```bash
scripts/tos-production-deploy.sh --scope frontend
```

5. Run live preflight:

```bash
scripts/tos-production-preflight.sh --live
```

6. Verify real production values with literal terminal output:

```bash
cat /opt/apps/tamiyouz-front/build/tos-release.json

curl -fsS https://tos.tamiyouz.com/tos-release.json

curl -fsS https://tos.tamiyouz.com/ -o /tmp/tos-p10-1-index.html

grep -o 'assets/index-[^" ]*\.js' /opt/apps/tamiyouz-front/build/index.html

grep -o 'assets/index-[^" ]*\.js' /tmp/tos-p10-1-index.html

MAIN_JS=$(grep -o 'assets/index-[^" ]*\.js' /tmp/tos-p10-1-index.html | head -n1)
curl -sk -o /dev/null -w 'PUBLIC_MAIN_JS_HTTP=%{http_code}\n' "https://tos.tamiyouz.com/$MAIN_JS"
```

Required proof:
- published release manifest is valid JSON
- public release manifest is valid JSON
- both manifests identify the same exact `mainJs`
- published index and public index identify the same exact `mainJs`
- the exact `mainJs` includes `assets/`
- exact public asset returns HTTP 200
- live preflight exits 0

---

## Commit

After all checks pass, create exactly one new local commit on top of `61caeb3`:

```text
fix(tnc): correct phase 10 release asset identity
```

DO NOT PUSH.

---

## Evidence discipline

Do not return polished summaries as verification.
Do not invent hashes, asset names, HTTP codes, timestamps, or PASS values.
Do not replace missing evidence with `YES`, `SUCCESS`, or placeholders.

For every requested field, use the real terminal value. If not proven, use `NOT_VERIFIED` and set `BLOCKER`.

## Final report format

Return exactly:

```text
BASE_HEAD=
ORIGIN_MAIN=
FILES_CHANGED=
RELEASE_MANIFEST_TRACKED=
PUBLISHED_RELEASE_JSON=
PUBLIC_RELEASE_JSON=
PUBLISHED_MAIN_JS=
PUBLIC_MAIN_JS=
PUBLIC_MAIN_JS_HTTP=
RELEASE_MAIN_JS_EXACT_MATCH=
PREFLIGHT_LIVE=
PREFLIGHT_LIVE_EXIT=
COMMIT_SHA=
WORKTREE=
PUSH_PERFORMED=NO
BLOCKER=
```
