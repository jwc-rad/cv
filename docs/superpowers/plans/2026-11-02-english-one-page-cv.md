# English One-Page CV PDF Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an English, portrait-free, exactly one-page A4 summary CV PDF alongside the existing full CV.

**Architecture:** Extend the existing static-site build to create an ignored HTML print source from the shared English CV, profile, and ORCID data plus a small summary configuration. Render that source with the existing Chromium PDF helper, expose the PDF from the English site, and enforce the one-page contract in output checks.

**Tech Stack:** Python 3.12 standard library, HTML/CSS, Chromium headless printing, `unittest`.

**Spec:** Approved conversational design from 2026-11-02; no separate repository spec.

## Global Constraints

- Keep the existing full English and Korean CV outputs unchanged.
- Add no external Python dependencies.
- Generate only an English summary PDF; its HTML source remains under ignored `preview/`.
- Include four appointments, all education and licenses, and four curated lead publications.
- Exclude portrait, address, internship, awards, full publications, and Korean summary.
- Fail validation if the summary PDF is not exactly one A4 page.

## Review Focus

- Missing, duplicate, or non-lead configured publication IDs must fail clearly.
- Curated publications must retain configured order regardless of ORCID order.
- User-controlled text must be HTML escaped and DOI links must remain usable.
- The English site must link both full and summary PDFs without adding the summary to Korean output.
- Content growth must create a second page and fail validation rather than clipping or shrinking invisibly.

---

### Task 1: Summary selection and HTML source

**Files:**
- Create: `content/cv.summary.en.json`
- Create: `tests/test_summary_cv.py`
- Create: `assets/summary.css`
- Modify: `scripts/build_site.py`

- [ ] Write failing unit tests for curated selection validation, ordering, HTML escaping, included content, and exclusions.
- [ ] Run the tests and confirm they fail because summary functions do not exist.
- [ ] Implement `select_summary_works(...)` and `build_summary_page(...)`, then write `preview/summary-en.html` during the normal build.
- [ ] Run the unit suite and confirm it passes.

### Task 2: PDF rendering and English-site link

**Files:**
- Modify: `content/cv.en.json`
- Modify: `scripts/build_site.py`
- Modify: `scripts/render_pdfs.py`
- Modify: `scripts/check_output.py`
- Modify: `tests/test_summary_cv.py`

- [ ] Write failing tests for the English-only download link and exact one-page output validation.
- [ ] Run the tests and confirm the expected failures.
- [ ] Add the English link, render target, and exact page-count check.
- [ ] Run the unit and generated-output checks.

### Task 3: Documentation and end-to-end verification

**Files:**
- Modify: `README.md`
- Modify: `.github/workflows/pages.yml`

- [ ] Document the new artifact and make the workflow run unit tests.
- [ ] Run the full Python 3.12 suite, site build, PDF rendering, and output checks.
- [ ] Rasterize and inspect the one-page PDF for legibility and clipping.
