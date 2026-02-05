# ADR-002: Keep SSI Filename Despite ORI Rebrand

**Date:** 2026-02-05
**Status:** Accepted
**Author:** Chindu Sreedharan

## Context

The index originally named "SSI" (Source & Substance Index) was rebranded to "ORI" (Original Reporting Index) in January 2026. The rebrand affected:
- Frontend display names (dashboard labels, popups)
- Public-facing documentation (README, methodology papers)
- User-visible terminology

However, the backend filenames remain as `ssi_*`:
- `ssi_score.py` (production scoring script)
- `metrics_ssi.json` (data file)
- `ssi_prompt_v2.1.md` (LLM prompt)
- `ssi_daily.yml.disabled` (workflow file)

## Decision

**Keep all SSI filenames in the codebase unchanged.**

## Rationale

1. **Stability over consistency:** Renaming would require changes across:
   - Python imports and function calls
   - Git history and commit messages
   - Workflow configurations (even if disabled)
   - Data file references in multiple scripts
   - Documentation cross-references

2. **Historical accuracy:** Git history shows the evolution from SSI → NGI → ORI. Keeping original filenames preserves this development narrative.

3. **No user impact:** End users never see backend filenames. All public-facing references correctly use "ORI".

4. **Legacy filename precedent:** Already documented in ADR-001 that `metrics_ssi.json` is a "legacy filename" for ORI data.

## Consequences

- Internal code references remain as `ssi_*`
- Comments in code should clarify: `# SSI (now ORI)`
- New developers need context (this ADR provides it)
- Future work should continue using SSI in backend, ORI in frontend

## Notes

This is consistent with ADR-001, which explicitly labels `metrics_ssi.json` as "ORI scores (legacy filename)".

Frontend successfully decouples display names from backend identifiers - no need for costly refactoring.
