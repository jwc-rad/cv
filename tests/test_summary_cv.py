import unittest

from scripts.build_site import build_summary_page, select_summary_works


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


if __name__ == "__main__":
    unittest.main()
