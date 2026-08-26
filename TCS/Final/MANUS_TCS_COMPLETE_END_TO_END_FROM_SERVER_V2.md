# TCS — One-Shot Completion From Production Server V2

## CRITICAL REPOSITORY DISTINCTION

`mohamedamouseo-a11y/TOS-Patchs` is ONLY the instruction/prompt repository. It is NOT the implementation target and MUST NOT receive TCS code commits.

The actual implementation repository is:
- GitHub target: `mohamedamouseo-a11y/TOS`
- Branch: `main` ONLY
- Production working copy: `/var/www/TOS`

All coding, testing, commits, and pushes MUST happen from inside `/var/www/TOS`.

When this prompt says PUSH, it means exactly:

```bash
cd /var/www/TOS
# commit implementation here
git push <authenticated TOS remote> main:main
```

The destination MUST resolve to `mohamedamouseo-a11y/TOS`.

NEVER push implementation code to `mohamedamouseo-a11y/TOS-Patchs`.
NEVER create a branch.
NEVER implement inside a clone of TOS-Patchs.

## Execution body

Now execute the full instructions from:

`TCS/Final/MANUS_TCS_COMPLETE_END_TO_END_V1.md`

Treat every repository/push reference in that file according to the distinction above:
- Prompt source = `TOS-Patchs`
- Working directory = `/var/www/TOS`
- Code repository = `mohamedamouseo-a11y/TOS`
- Push destination = `mohamedamouseo-a11y/TOS/main`

Manus owns the remaining TCS code, fixes, tests, commits, push from the production TOS server, deployment, and final report.

Return:
`TCS_COMPLETE_END_TO_END_V2_REPORT.zip`

The final report must include the exact sanitized output of:

```bash
cd /var/www/TOS
pwd
git remote -v | sed -E 's#(https://)[^/@]+@#\1***@#g'
git branch --show-current
git rev-parse HEAD
```

and must state explicitly:

```text
IMPLEMENTATION_WORKDIR=/var/www/TOS
IMPLEMENTATION_REPO=mohamedamouseo-a11y/TOS
IMPLEMENTATION_BRANCH=main
PROMPT_REPO=mohamedamouseo-a11y/TOS-Patchs
CODE_PUSHED_TO_PATCH_REPO=NO
PUSH_FROM_TOS_SERVER=YES
```
