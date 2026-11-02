# Korean One-Page CV Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Korean, portrait-free, exactly one-page A4 summary CV matching the existing English summary.

**Architecture:** Generalize the existing summary HTML builder to choose labels, title, font class, and generated-date format from `cv["lang"]`. Feed it a Korean summary config using the same curated ORCID IDs, render a fourth PDF through the existing Chromium pipeline, and expose it only from the Korean site.

**Tech Stack:** Python 3.12 standard library, HTML/CSS, Chromium headless printing, `unittest`.

**Spec:** `docs/superpowers/specs/2026-11-02-korean-one-page-cv-design.md`

## Global Constraints

- Preserve the existing full Korean/English CVs and English summary PDF.
- Use Korean profile, appointment, education, license, label, and date text.
- Keep publication titles, journals, DOI metadata, and citations in English.
- Use the same four curated ORCID IDs and four-entry appointment limit as the English summary.
- Produce exactly one A4 portrait page without portrait, address, internship, awards, or full publication list.
- Keep Python 3.12 and add no external dependencies.

## Review Focus

- English summary output must remain unchanged apart from shared markup structure.
- Korean and English summary configs must resolve the same four publications in the same order.
- Korean summary headings and date must not fall back to English.
- Korean site must link only the Korean summary; English site must continue linking only the English summary.
- Both summary PDFs must independently fail validation when not exactly one A4 portrait page.

---

### Task 1: Bilingual Summary Source and Site Links

**Files:**
- Create: `content/cv.summary.ko.json`
- Modify: `content/cv.ko.json`
- Modify: `scripts/build_site.py`
- Modify: `assets/summary.css`
- Modify: `tests/test_summary_cv.py`

**Interfaces:**
- Consumes: existing `build_summary_page(profile, cv, orcid, overrides, summary_config) -> str` and curated English summary config.
- Produces: `preview/summary-ko.html` plus language-specific site links to `jae-won-choi-cv-summary-{lang}.pdf`.

- [ ] Write failing tests asserting Korean headings, Korean generated-date text, Korean career data, English publication titles, the Korean-only download link, and retention of the English-only link.
- [ ] Run `CHROME_PATH=<browser> PYENV_VERSION=3.12.10 python -m unittest tests.test_summary_cv -v`; expect failures because the renderer and Korean page are English-only.
- [ ] Generalize summary labels/date/body language in `build_summary_page`, add the Korean config and label, emit both preview sources, and add a Korean system-font stack.
- [ ] Run the full unit suite and confirm all tests pass.
- [ ] Commit with `feat(cv): 한글 1페이지 요약 원본 추가`.

### Task 2: Korean PDF Rendering, Validation, and Documentation

**Files:**
- Modify: `scripts/render_pdfs.py`
- Modify: `scripts/check_output.py`
- Modify: `scripts/editor_server.py`
- Modify: `README.md`
- Modify: `tests/test_summary_cv.py`

**Interfaces:**
- Consumes: `preview/summary-ko.html` from Task 1.
- Produces: `dist/downloads/jae-won-choi-cv-summary-ko.pdf`, validated as exactly one A4 portrait page.

- [ ] Write a failing test proving both summary paths are passed to exact-one-page A4 validation.
- [ ] Run the targeted test and confirm it fails because only the English summary is checked.
- [ ] Add the Korean render target, independent validation/reporting, editor messaging, and README artifact documentation.
- [ ] Run the full unit suite, build both summary sources, render all four PDFs, and run output checks.
- [ ] Rasterize and inspect the Korean PDF for Korean glyph rendering, legibility, clipping, and one-page layout.
- [ ] Commit with `feat(cv): 한글 1페이지 요약 PDF 추가`.
