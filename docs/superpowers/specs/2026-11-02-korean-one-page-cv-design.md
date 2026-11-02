# Korean One-Page CV Design

## Intent

Add a Korean, portrait-free, exactly one-page A4 summary CV that matches the existing English summary. The Korean PDF is for the same broad professional use and should feel like the Korean counterpart of the English artifact rather than a separate design.

## Content

- Use `content/cv.ko.json` for the Korean name, role, affiliation, profile, appointments, education, and licenses.
- Include the first four appointments, all education and licenses, and the same four curated ORCID publications as the English summary.
- Keep official publication titles, journal names, DOI metadata, and abbreviated citations in English.
- Localize section labels, research interests, and the generated date into Korean.
- Continue excluding portrait, postal address, internship, awards, and the full publication list.

## Approach

Generalize the existing `build_summary_page` path into one bilingual renderer with language-specific labels and date formatting. Add a Korean summary configuration and print source, render `jae-won-choi-cv-summary-ko.pdf`, and expose it next to the full Korean CV link. The rejected alternative was a copied Korean renderer, which would duplicate layout and validation logic.

## Constraints and Acceptance

- Preserve the existing English summary output and full Korean/English CVs.
- Reuse the current A4 stylesheet, adding only a Korean font stack where needed.
- Validate both summary PDFs as exactly one A4 portrait page.
- Add regression coverage for Korean localization, English publication titles, Korean-only site exposure, and PDF validation.
- Keep Python 3.12 and the dependency-free Chromium rendering pipeline.
