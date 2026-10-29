# UI/UX Wizard Implementation Plan

> Use superpowers:executing-plans to implement task-by-task.

**Goal:** Deliver the approved four-step demo workflow and downloadable Excel template.
**Architecture:** Keep existing state/API modules; add a wizard controller that gates navigation using state, moves the single map between visible steps, and preserves mounted forms.
**Tech Stack:** Existing vanilla JS/CSS/HTML, openpyxl, pytest, Playwright.
**Spec:** docs/superpowers/specs/2026-10-29-ui-ux-wizard-design.md

## Global Constraints
- Work in the user's chosen codex/ui-ux-improvements checkout.
- Keep session-only data and existing grouping algorithm/API validation.
- Template headers: Há» vÃ  tÃªn, Giá»›i tÃ­nh, NÆ¡i á»Ÿ Ä‘á»ƒ há»c táº­p, CÆ° xÃ¡/Khu vá»±c.

## Review Focus
- Reimport invalidates results and locks subsequent steps.
- Location edits invalidate results without losing entered data.
- Map resizes when shown after being hidden.
- Gender dropdown must not create 1,000 empty imported rows.
- Mobile navigation and tables must not overflow the viewport.

## Task 1: Template
- [x] Add tests/test_excel_template.py: exact headers, blank template rejected as empty, filled template accepted, dropdown present.
- [x] Run test red; create scripts/create_import_template.py and frontend/templates/danh-sach-sinh-vien.xlsx; run test green.

## Task 2: Wizard
- [x] Add scripts/check_wizard_browser.py covering initial gate, template download, real import/geocoding/grouping/export, back navigation and stale-result invalidation; run red.
- [x] Add frontend/js/wizard.js initializeWizard(), using state.canGeocode, allLocationsVerified(), state.groupingResult and existing change events.
- [x] Update index.html and app.js; add wizard.css with responsive stepper, template panel, cards, buttons and table styles. Move group-results outside grouping-panel; move the map between location and results hosts.
- [x] Add map visibility event handling to map.js; run browser check green with existing offline provider.

## Task 3: Verification
- [x] Run pytest suite, inspect desktop/mobile screenshots and browser errors; review diff for regressions.
- [x] Record results and hand off changes for user review.
