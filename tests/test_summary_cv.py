import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.build_site import build_page, build_summary_page, select_summary_works, summary_author_markup
from scripts.check_output import check_pdf
from scripts.render_pdfs import find_browser


class SummaryPublicationSelectionTests(unittest.TestCase):
    def setUp(self):
        self.works = [
            {
                "put_code": str(code),
                "title": f"Paper {code}",
                "journal": "Journal",
                "date": {"year": "2026"},
                "contributors": [{"name": "Jae Won Choi"}],
                "external_ids": {"doi": {"value": f"10.1000/{code}", "url": f"https://doi.org/10.1000/{code}"}},
            }
            for code in (4, 3, 2, 1)
        ]

    def test_preserves_configured_order_instead_of_orcid_order(self):
        selected = select_summary_works(self.works, {}, ["1", "2", "3", "4"])
        self.assertEqual([work["put_code"] for work in selected], ["1", "2", "3", "4"])

    def test_rejects_missing_publication(self):
        with self.assertRaisesRegex(ValueError, "Summary publication not found: 9"):
            select_summary_works(self.works, {}, ["1", "2", "3", "9"])

    def test_rejects_duplicate_publication(self):
        with self.assertRaisesRegex(ValueError, "four unique publication IDs"):
            select_summary_works(self.works, {}, ["1", "2", "2", "4"])

    def test_rejects_non_lead_publication(self):
        non_lead = dict(self.works[0], contributors=[{"name": "Another Author"}])
        works = [non_lead, *self.works[1:]]
        with self.assertRaisesRegex(ValueError, "not marked as lead: 4"):
            select_summary_works(works, {}, ["1", "2", "3", "4"])


class SummaryPageTests(unittest.TestCase):
    def test_renders_required_content_and_excludes_full_cv_only_content(self):
        profile = {
            "orcid_id": "0000-0002-5937-7238",
            "photo": "assets/profile.png",
            "contact": {"emails": ["doctor@example.com"], "address_en": "Private postal address"},
            "links": {
                "orcid": "https://orcid.org/0000-0002-5937-7238",
                "google_scholar": "https://scholar.google.com/example",
            },
        }
        cv = {
            "lang": "en",
            "name": "Jae Won Choi, M.D.",
            "role": "Clinical Assistant Professor",
            "affiliation": "Seoul National University Hospital",
            "bio": "Pediatric radiologist <script>alert(1)</script>",
            "focus": ["Pediatric Radiology", "Artificial Intelligence"],
            "experience": [
                {"title": f"Appointment {index}", "organization": "Hospital", "period": str(index), "detail": ""}
                for index in range(1, 6)
            ],
            "education": [{"title": "M.D.", "organization": "SNU", "period": "2016", "detail": ""}],
            "licenses": [{"title": "Medical License", "period": "2016 – Present"}],
            "awards": [{"title": "Excluded Award", "organization": "Org", "date": "2024", "detail": ""}],
        }
        works = [
            {
                "put_code": str(code),
                "title": f"Selected Paper {code}",
                "journal": "Pediatric Radiology",
                "date": {"year": "2026"},
                "contributors": [{"name": "Jae Won Choi"}],
                "external_ids": {"doi": {"value": f"10.1000/{code}", "url": f"https://doi.org/10.1000/{code}"}},
            }
            for code in range(1, 5)
        ]
        html = build_summary_page(
            profile,
            cv,
            {"works": works},
            {},
            {"experience_limit": 4, "selected_publication_put_codes": ["1", "2", "3", "4"]},
        )

        self.assertIn("Jae Won Choi, M.D.", html)
        self.assertIn("Appointment 4", html)
        self.assertNotIn("Appointment 5", html)
        self.assertIn("Selected Paper 1", html)
        self.assertIn("https://doi.org/10.1000/1", html)
        self.assertIn("Pediatric Radiology", html)
        self.assertIn("Medical License", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertNotIn("Private postal address", html)
        self.assertNotIn("Excluded Award", html)
        self.assertNotIn("profile.png", html)

    def test_full_site_links_summary_pdf_from_english_only(self):
        root = Path(__file__).resolve().parents[1]
        profile = json.loads((root / "content" / "profile.json").read_text(encoding="utf-8"))
        orcid = json.loads((root / "data" / "orcid.json").read_text(encoding="utf-8"))
        overrides = json.loads((root / "content" / "publication_overrides.json").read_text(encoding="utf-8"))
        en = json.loads((root / "content" / "cv.en.json").read_text(encoding="utf-8"))
        ko = json.loads((root / "content" / "cv.ko.json").read_text(encoding="utf-8"))

        english_html = build_page(profile, en, orcid, overrides)
        korean_html = build_page(profile, ko, orcid, overrides)

        self.assertIn("downloads/jae-won-choi-cv-summary-en.pdf", english_html)
        self.assertIn("One-page CV", english_html)
        self.assertNotIn("jae-won-choi-cv-summary-en.pdf", korean_html)

    def test_corresponding_author_citation_uses_actual_first_author(self):
        work = {
            "contributors": [{"name": "Another Author"}, {"name": "Jae Won Choi"}],
        }

        self.assertEqual(summary_author_markup(work), "Another Author, et al.")

    def test_mobile_download_links_span_the_profile_grid(self):
        root = Path(__file__).resolve().parents[1]
        browser = find_browser(os.environ.get("CHROME_PATH"))
        stylesheet = (root / "assets" / "site.css").resolve().as_uri()
        document = f"""<!doctype html>
<html><head><meta name="viewport" content="width=device-width"><link rel="stylesheet" href="{stylesheet}"></head>
<body><aside class="author-profile"><div class="cv-downloads"><a class="cv-link">Full CV</a><a class="cv-link">One-page CV</a></div></aside>
<script>window.addEventListener("load", () => {{
  const style = getComputedStyle(document.querySelector(".cv-downloads"));
  document.documentElement.dataset.grid = `${{style.gridColumnStart}}/${{style.gridColumnEnd}}`;
}});</script></body></html>"""

        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "mobile.html"
            source.write_text(document, encoding="utf-8")
            completed = subprocess.run(
                [
                    str(browser),
                    "--headless=new",
                    "--disable-gpu",
                    "--no-sandbox",
                    "--allow-file-access-from-files",
                    "--window-size=390,800",
                    "--dump-dom",
                    source.resolve().as_uri(),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('data-grid="1/-1"', completed.stdout)


class SummaryPdfValidationTests(unittest.TestCase):
    def test_rejects_summary_pdf_with_more_than_one_page(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "summary.pdf"
            path.write_bytes(b"%PDF" + b"x" * 5_000 + b"/Type /Page /Type /Page")

            with self.assertRaisesRegex(AssertionError, "Expected 1 PDF page, found 2"):
                check_pdf(path, expected_pages=1)

    def test_rejects_summary_pdf_that_is_not_a4_portrait(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "summary.pdf"
            path.write_bytes(b"%PDF" + b"x" * 5_000 + b"/Type /Page /MediaBox [0 0 612 792]")

            with self.assertRaisesRegex(AssertionError, "Expected A4 portrait PDF page"):
                check_pdf(path, expected_pages=1, expected_page_size="A4")


if __name__ == "__main__":
    unittest.main()
