# PATCH-RAMZY-SMART-TASK-V3-PHASE-4-R6-PLACEHOLDER-ONLY

Baseline: 7ac58a2eeb3499eee041dae21189d2ad4db78907

One-line acceptance fix only.

In frontend/src/components/RamzyAssistant.jsx, change the empty assignee <option> text to:
- if !smartTask.project:
  - EN: Select a project first
  - AR: اختر المشروع أولاً
- else:
  - EN: Select...
  - AR: اختر...

Do not change anything else.
Build + commit only. Do not push.
