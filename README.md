# BUzz Metrics

A prototype analytics dashboard for a student newsroom at Bournemouth University, UK. Developed as part of research into automated journalism quality measurement.

**[Live Dashboard](https://chindusree.github.io/buzz-metrics/)**

---

## What This Is

An experimental system that extracts and visualises sourcing patterns from student journalism. The dashboard allows filtering and exploration of article data — it does not grade individual student work.

**Philosophy:** Guidance, not grading.

---

## The Three Indices

| Index | Measures |
|-------|----------|
| **SEI** (Source Equity Index) | Sourcing diversity — who speaks, who explains, who's absent |
| **ORI** (Original Reporting Index) | Newsgathering effort — original reporting vs churnalism |
| **BNS** (Breaking News Score) | Speed to audience vs professional outlets |

---

## Dataset

January 2026 pilot: 312 articles from BUzz newsdays.

- **SEI:** 266 scored, 46 exempt (match reports, court registers, breaking news, live blogs)
- **ORI:** 295 scored, 17 exempt (video/audio only)
- **BNS:** 17 breaking news articles

---

## Validation

A 10% stratified sample was validated using Inter-Model Reliability (IMR) — comparing outputs from two independent LLMs (Groq/Llama and Anthropic/Claude).

| Index | Sample | Agreement |
|-------|--------|-----------|
| SEI | N=31 | 84.5% |
| ORI | N=30 | 85.0% |

This validates extraction consistency, not accuracy of the underlying methodology.

---

## Architecture

Three JSON files, merged on frontend:

| File | Contents |
|------|----------|
| `metrics_sei.json` | Article metadata + SEI scores |
| `metrics_ssi.json` | ORI scores (legacy filename) |
| `metrics_bns.json` | Breaking news scores |

See [ADR-001](docs/decisions/001-data-architecture.md) for rationale.

---

## Repository Structure
```
buzz-metrics/
├── scraper/           # Python scripts + LLM prompts
├── data/              # Production JSON
├── docs/              # GitHub Pages dashboard
├── analysis/          # Investigation reports
└── .github/workflows/ # Automation
```

---

## Setup

```bash
git clone https://github.com/Chindusree/buzz-metrics.git
cd buzz-metrics/scraper
pip install -r requirements.txt
```

---

## Methodology

Working papers (in preparation):

- **SEI:** *Who speaks, who explains, who's absent: A context-adaptive index for sourcing integrity in journalism*
- **ORI:** *Measuring newsgathering labour in student journalism*
- **IMR:** *Inter-Model Reliability: A consistency protocol for automated content analysis*

---

## Limitations

- **Prototype:** Research tool, not production system
- **Gender inference:** Name-based, limited beyond binary
- **Validation:** Sample-based, not comprehensive
- **Scope:** Measures sourcing patterns, not writing quality or news judgment

---

## Citation

```bibtex
@misc{buzzmetrics2026,
  author = {Sreedharan, Chindu},
  title = {BUzz Metrics: Automated Quality Analytics for Student Journalism},
  year = {2026},
  institution = {Bournemouth University},
  url = {https://github.com/Chindusree/buzz-metrics}
}
```

---

## License

All rights reserved. This repository is public for transparency and academic review.

For licensing enquiries, contact csreedharan@bournemouth.ac.uk

---

## Acknowledgements

Developed at Bournemouth University.
