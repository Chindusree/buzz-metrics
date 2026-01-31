# ADR-001: Separate Index Files vs Unified Data File

**Date:** January 2026
**Status:** Accepted
**Author:** Chindu Sreedharan

## Context

BUzz Metrics calculates multiple indices (SEI, SSI, BNS) for student journalism articles. We needed to decide whether to store all data in one file or separate files per index.

## Decision

**Use separate files per index.**

| File | Contents |
|------|----------|
| `metrics_sei.json` | Base article data + SEI scores |
| `metrics_ssi.json` | SSI scores and components |
| `metrics_bns.json` | BNS scores (BREAKING only) |

## Rationale

1. **Race condition prevention:** During active newsdays, multiple workflows run frequently (scraper every hour, SEI at 13:00/16:00, SSI at 13:30/16:30). Separate files eliminate write conflicts.

2. **Fault isolation:** If SSI scoring fails mid-run, SEI data remains intact.

3. **Clear ownership:** Each script owns its output file. Single responsibility.

4. **Negligible frontend cost:** Merging 2-3 small JSON files client-side adds ~10 lines of code and <50ms latency.

## Alternatives Considered

**Unified file with staggered scheduling:** Cleaner mental model, but higher corruption risk and requires strict scheduling discipline. Rejected during active newsday period.

## Consequences

- Frontend must merge files by article URL
- Each index workflow is fully independent
- Adding new indices requires new file + merge logic
