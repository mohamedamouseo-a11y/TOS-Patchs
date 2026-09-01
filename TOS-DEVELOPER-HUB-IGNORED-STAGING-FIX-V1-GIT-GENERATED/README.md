# TOS Developer Hub Ignored Staging Fix V1

Baseline TOS commit: `63f59932776e29e32bacdf5214744d2662a3b8e3`

Target: `backend/src/services/githubAdvanced.service.js`

## Problem

The Developer Hub `stageSafeChanges()` flow re-runs `git add -A -- <path>` for every safe dirty path. When a tracked runtime file has intentionally been removed from the Git index with `git rm --cached` but still exists on disk under a new `.gitignore` rule, Git treats the worktree copy as ignored and aborts staging with:

`The following paths are ignored by one of your .gitignore files: backend/.pm2`

Using `git add -f` would be wrong because the PM2 runtime files are intentionally excluded from source control.

## Fix

The patch keeps the current security scan and reviewed-push workflow intact, but before staging it:

1. Reads the already-staged diff.
2. Detects staged deletion paths.
3. For a staged deletion whose local worktree copy is ignored by Git, preserves the staged deletion and does **not** pass that path back to `git add -A`.
4. Stages the remaining safe source changes normally.
5. Re-scans the complete staged diff before commit as before.

This allows the intentional deletions of `backend/.pm2/module_conf.json` and `backend/.pm2/touch` to stay staged while the runtime copies remain physically on the server.

No force-add is used.

## Apply

```bash
rm -rf /tmp/TOS-Patchs
git clone https://github.com/mohamedamouseo-a11y/TOS-Patchs.git /tmp/TOS-Patchs
bash /tmp/TOS-Patchs/TOS-DEVELOPER-HUB-IGNORED-STAGING-FIX-V1-GIT-GENERATED/run_developer_hub_ignored_staging_fix_v1.sh /var/www/TOS
```

The runner does not commit or push. It refuses to patch a different TOS HEAD or a locally modified target service file, while allowing the existing Phase 3/Phase 4 working-tree changes in other files.

After applying, restart the existing `tamiyouz-system` PM2 service, refresh Developer Hub, run a new **Review**, then **Execute Push** from the normal TOS UI.
