# TOS-TCRM-CLIENT-IDENTITY-DUPLICATE-GUARD-V1-R1-CRMCLIENT-FIRST-GIT-GENERATED

Small follow-up patch for the already-applied V1 duplicate guard.

## Change
Makes `crmClientId` the first-priority match in the existing `tos_crm_project_deliveries` lookup, with `sourceKey` retained as secondary fallback.

## Preserved
- V1 legacy-project duplicate guard
- mapped-client update path
- zero-candidate create path
- existing schema

## Not included
- no auto-adoption
- no duplicate cleanup
- no DB unique constraint yet
- no Brief/Services/Team mapping changes
- no deploy/restart/push

Target file:
`backend/src/routes/crmProjectsIntegration.routes.js`
