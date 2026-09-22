# TOS Task Description Mixed Direction Fix V1

Fixes mixed Arabic/English text direction in task descriptions and comments, especially Design Request descriptions.

## Root cause

The rich-text editor used `dir="auto"` only at the editor root, while Design Request blocks were forced to the UI language direction. On an English UI, Arabic values were therefore rendered inside an LTR block and words/links/punctuation appeared in the wrong visual order.

## Fix

- Auto-detect direction per rich-text block/value.
- Design Request labels/headings keep the UI direction.
- Design Request values use `dir="auto"` + `unicode-bidi: plaintext`.
- Editor and read-only rich-text display both receive auto direction.
- Manual RTL/LTR toolbar choices are marked and preserved.
- Existing text content is not rewritten.
- No backend/database changes.

Apply:

```bash
python3 TOS-TASK-DESCRIPTION-MIXED-DIRECTION-FIX-V1/apply_task_description_mixed_direction_fix_v1.py /var/www/TOS
```
