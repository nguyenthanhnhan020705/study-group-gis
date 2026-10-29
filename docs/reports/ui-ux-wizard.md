# UI/UX wizard — 2026-10-29

Implemented on `codex/ui-ux-improvements`: four-step navigation, downloadable four-column workbook, state-dependent navigation gates, responsive layout, shared map relocation, and preserved session data on back navigation.

## Verification

- `.venv/Scripts/python.exe -m pytest -q`: 244 passed (19.10 seconds).
- `.venv/Scripts/python.exe scripts/check_wizard_browser.py`: passed real local import, geocoding-provider fixture, grouping/filter/export, template download, back navigation, failed regeneration, invalidation, mobile width and JavaScript-error checks.
- Browser uses actual Leaflet 1.9.4 from the existing `.local-tests/phase-5/leaflet-1.9.4.js` and `.css` cache. Tile images and external geocoding are synthetic fixtures; this run does not certify live provider availability.
- Desktop and mobile screenshots inspected in `.local-tests/wizard/`.
- `git diff --check`: passed.

## Review fixes

Independent code review identified two issues, both reproduced by failing browser checks and fixed:

1. Ordinary state changes must not trigger map visibility fitting and override candidate preview. Resize/fit is now limited to showing or relocating the map.
2. Regenerating groups clears the prior result and immediately notifies navigation, including when the request fails.

## Decisions

- Retained user-selected feature branch and checkout.
- Retained optional Cư xá/Khu vực and compatible three-column imports; downloaded template always contains all four columns.
- Kept existing API contracts and grouping algorithm.
- Existing pre-wizard browser scripts assume all controls are visible together; use the new wizard check for the step-based UI.
