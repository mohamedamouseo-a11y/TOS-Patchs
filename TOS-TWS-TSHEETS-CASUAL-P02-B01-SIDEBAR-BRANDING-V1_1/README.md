# TSheets Casual — P02 / B01 / V1_1

Hotfix for long loading introduced by P02-B01 V1.

## Fix
- removes the continuous MutationObserver;
- removes full body text walking;
- keeps branding retries bounded to 6 attempts over 1.8s;
- keeps the T-Sheets logo/wordmark and click guard;
- preserves the sidebar child from P02 V1;
- does not rebuild Casual Sheets or Univer.

## Changed file
- frontend/src/pages/tws/TSheetsCasualLab.jsx

No backend, DB, commit, or push.
