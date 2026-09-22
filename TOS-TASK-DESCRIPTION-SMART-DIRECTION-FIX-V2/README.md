# TOS Task Description Smart Direction Fix V2

Fixes the remaining mixed Arabic/English direction issue after V1.

## Why V1 was not enough

Browser `dir="auto"` uses the **first strong character** of a paragraph. If an Arabic paragraph begins with an English token such as `caption`, the whole paragraph becomes LTR even when most of the content is Arabic.

## V2

- Detects the dominant script for each rich-text block.
- Arabic-majority block => RTL.
- Latin-majority block => LTR.
- URLs and email addresses are ignored while deciding direction.
- Uses `unicode-bidi: isolate` so an initial English token cannot override the chosen paragraph base direction.
- Handles direct editor DIV lines as well as paragraphs/list items/design-request values.
- Manual RTL/LTR toolbar choices remain authoritative.
- Does not rewrite text content.

Requires V1 to already be applied on the live TOS worktree.
