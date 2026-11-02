#!/usr/bin/env python3
"""Run lightweight integrity checks on the generated website and PDFs."""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


class LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        key = "src" if tag in {"img", "script"} else "href" if tag in {"a", "link"} else ""
        if key and attributes.get(key):
            self.links.append(str(attributes[key]))


def check_html(path: Path, expected_lang: str) -> None:
    text = path.read_text(encoding="utf-8")
    required = [f'<html lang="{expected_lang}">', json.loads((ROOT / "content" / "profile.json").read_text(encoding="utf-8"))["orcid_id"], "data-pub-group"]
    for marker in required:
        if marker not in text:
            raise AssertionError(f"Missing {marker!r} in {path}")

    collector = LinkCollector()
    collector.feed(text)
    missing: list[str] = []
    for raw in collector.links:
        split = urlsplit(raw)
        if split.scheme or split.netloc or raw.startswith(("#", "mailto:", "tel:")):
            continue
        local = unquote(split.path)
        target = (path.parent / local).resolve() if local else path.resolve()
        if target.is_dir():
            target = target / "index.html"
        if not target.exists():
            missing.append(raw)
    if missing:
        raise AssertionError(f"Broken local links in {path}: {missing}")


def check_pdf(
    path: Path, expected_pages: int | None = None, expected_page_size: str | None = None
) -> int:
    data = path.read_bytes()
    if len(data) < 5_000 or not data.startswith(b"%PDF"):
        raise AssertionError(f"Invalid PDF: {path}")
    pages = len(re.findall(rb"/Type\s*/Page(?!s)\b", data))
    if pages < 1:
        raise AssertionError(f"Could not find PDF pages in {path}")
    if expected_pages is not None and pages != expected_pages:
        raise AssertionError(f"Expected {expected_pages} PDF page, found {pages}: {path}")
    if expected_page_size is not None:
        if expected_page_size != "A4":
            raise ValueError(f"Unsupported expected PDF page size: {expected_page_size}")
        media_boxes = re.findall(rb"/MediaBox\s*\[\s*([^\]]+)\]", data)
        if not media_boxes:
            raise AssertionError(f"Could not find PDF page dimensions in {path}")
        coordinates = [float(value) for value in media_boxes[0].split()]
        if len(coordinates) != 4:
            raise AssertionError(f"Invalid PDF MediaBox in {path}")
        width = abs(coordinates[2] - coordinates[0])
        height = abs(coordinates[3] - coordinates[1])
        if abs(width - 595.28) > 1.0 or abs(height - 841.89) > 1.0:
            raise AssertionError(
                f"Expected A4 portrait PDF page, found {width:.2f} × {height:.2f} points: {path}"
            )
    return pages


def main() -> int:
    check_html(DIST / "index.html", "ko")
    check_html(DIST / "en" / "index.html", "en")
    ko_pages = check_pdf(DIST / "downloads" / "jae-won-choi-cv-ko.pdf")
    en_pages = check_pdf(DIST / "downloads" / "jae-won-choi-cv-en.pdf")
    summary_pages = check_pdf(
        DIST / "downloads" / "jae-won-choi-cv-summary-en.pdf",
        expected_pages=1,
        expected_page_size="A4",
    )
    print(
        "Output checks passed: "
        f"Korean PDF {ko_pages} pages, English PDF {en_pages} pages, English summary PDF {summary_pages} page"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
