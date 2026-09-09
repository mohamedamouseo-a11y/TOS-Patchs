# TOS Ramzy Typing Performance V1

Target: `frontend/src/components/RamzyAssistant.jsx`

Baseline TOS commit: `509c51eeab1a9b880d902aac5082aa6124996c9b`

Target blob guard: `138c04ef2959ba3d3e99a767653311958dae1195`

## Problem confirmed in source
Ramzy's composer was controlled by parent React state on every keystroke. The same textarea also used both `onChange` and `onInput`, synchronous autosize read `scrollHeight` on each input, and the Help Center bridge effect depended on the full input string.

Because `RamzyAssistant.jsx` also renders the full conversation, markdown responses, approvals, voice controls, and the panel, typing caused unnecessary parent work.

## Patch
The runner:
- moves live composer text to a ref/uncontrolled textarea path
- updates React state only when the composer changes between empty and non-empty
- removes the duplicate `onChange` + `onInput` state path
- batches textarea autosize through `requestAnimationFrame`
- stops Help Center listener re-registration on every keystroke
- keeps voice dictation and Help Center prompt injection synchronized
- adds an IME composition guard so Enter does not submit during Arabic/IME composition
- preserves Enter-to-send and Shift+Enter newline behavior
- runs `git diff --check`
- builds the frontend
- deploys the built frontend using the established TOS live deployment path
- verifies the live JS bundle matches the built bundle
- never commits or pushes the TOS source

## Run
See `OPENHANDS_PROMPT.md`.
