# TOS UX/UI — Phase 04.1 Design Queue Performance V1

Performance-only patch for `Workspace → Design Queue`.

Fixes:
- removes the explicit Design Queue `window.focus` refetch that caused browser-tab return refreshes;
- keeps BroadcastChannel/storage/custom-event refreshes but makes them silent (no full loading-state flicker);
- adds a language-only preferences context and memoizes DesignQueuePage so theme toggles do not re-render the heavy queue tree when its props are unchanged;
- preserves V6 CSS byte-for-byte and does not change Design Queue business logic or visual design.

Run:

```bash
python3 TOS-UXUI-PHASE-04-1-DESIGN-QUEUE-PERFORMANCE-V1/apply_phase04_1_design_queue_performance_v1.py /var/www/TOS
```

The script runs `npm run build`, deploys `frontend/dist` into `/opt/apps/tamiyouz-front/build`, validates Nginx, and does not commit or push TOS.
