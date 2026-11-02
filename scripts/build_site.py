#!/usr/bin/env python3
"""Build a dependency-free bilingual static CV site from JSON content."""

from __future__ import annotations

import html
import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


KST = timezone(timedelta(hours=9))


def build_date() -> datetime:
    """Date the site and PDFs were generated, in Korea Standard Time."""
    return datetime.now(KST)


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
ASSETS = ROOT / "assets"
DATA = ROOT / "data"
DIST = ROOT / "dist"
PREVIEW = ROOT / "preview"

TARGET_NAME_VARIANTS = {"jae won choi", "jaewon choi", "jae-won choi", "choi jae won", "choi jaewon", "choi jae-won", "jw choi", "j w choi", "choi jw", "choi j w"}
PDF_SLUG = "jae-won-choi-cv"
SUMMARY_PDF_NAME = "jae-won-choi-cv-summary-en.pdf"
BRAND = "Jae Won Choi"


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def e(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def e_multiline(value: Any) -> str:
    return e(value).replace("\n", "<br>")


def normalize_name(raw: Any) -> str:
    return " ".join(str(raw or "").lower().replace(",", " ").split())


def timeline(items: list[dict[str, str]]) -> str:
    rows = []
    for item in items:
        detail = f'<p class="item-detail">{e(item.get("detail"))}</p>' if item.get("detail") else ""
        rows.append(
            f"""<li class="timeline-item">
              <span class="item-period">{e(item.get('period'))}</span>
              <h3 class="item-title">{e(item.get('title'))}</h3>
              <p class="item-organization">{e(item.get('organization'))}</p>
              {detail}
            </li>"""
        )
    return '<ol class="timeline">' + "".join(rows) + "</ol>"


def clean_list(items: list[dict[str, str]]) -> str:
    return '<ul class="clean-list">' + "".join(
        f'<li><strong>{e(item.get("title"))}</strong><span>{e(item.get("period"))}</span></li>' for item in items
    ) + "</ul>"


def author_markup(work: dict[str, Any], is_lead: bool, star_label: str = "") -> str:
    authors = []
    for contributor in work.get("contributors") or []:
        raw_name = str(contributor.get("name") or "").strip()
        escaped = e(raw_name)
        if normalize_name(raw_name) in TARGET_NAME_VARIANTS:
            star = ""
            if is_lead:
                label_html = f' <span class="lead-star-label">({e(star_label)})</span>' if star_label else ""
                star = f'<span class="lead-star" aria-hidden="true">*</span>{label_html}'
            escaped = f"<strong>{escaped}</strong>{star}"
        authors.append(escaped)
    return ", ".join(authors)


def is_lead_work(work: dict[str, Any], overrides: dict[str, Any]) -> bool:
    put_code = str(work.get("put_code") or "")
    override = overrides.get(put_code) or {}
    if "lead" in override:
        return bool(override["lead"])
    contributors = work.get("contributors") or []
    if not contributors:
        return False
    return normalize_name(contributors[0].get("name")) in TARGET_NAME_VARIANTS


def select_summary_works(
    works: list[dict[str, Any]], overrides: dict[str, Any], put_codes: list[str]
) -> list[dict[str, Any]]:
    normalized_codes = [str(code) for code in put_codes]
    if len(normalized_codes) != 4 or len(set(normalized_codes)) != 4:
        raise ValueError("Summary CV requires four unique publication IDs")

    by_code = {str(work.get("put_code") or ""): work for work in works}
    selected = []
    for put_code in normalized_codes:
        work = by_code.get(put_code)
        if work is None:
            raise ValueError(f"Summary publication not found: {put_code}")
        if not is_lead_work(work, overrides):
            raise ValueError(f"Summary publication is not marked as lead: {put_code}")
        selected.append(work)
    return selected


def summary_author_markup(work: dict[str, Any]) -> str:
    contributors = work.get("contributors") or []
    if not contributors:
        return "<strong>Choi JW</strong>, et al."
    first_author = str(contributors[0].get("name") or "").strip()
    if normalize_name(first_author) in TARGET_NAME_VARIANTS:
        return "<strong>Choi JW</strong>, et al."
    return f"{e(first_author)}, et al."


def build_summary_page(
    profile: dict[str, Any],
    cv: dict[str, Any],
    orcid: dict[str, Any],
    overrides: dict[str, Any],
    summary_config: dict[str, Any],
) -> str:
    selected_works = select_summary_works(
        orcid.get("works") or [], overrides, summary_config.get("selected_publication_put_codes") or []
    )
    experience_limit = int(summary_config.get("experience_limit") or 0)
    experience = cv.get("experience", [])[:experience_limit]
    generated = build_date()

    def compact_items(items: list[dict[str, str]]) -> str:
        rows = []
        for item in items:
            organization = item.get("organization")
            organization_html = (
                f'<span class="summary-organization">{e(organization)}</span>' if organization else ""
            )
            rows.append(
                '<li>'
                f'<span class="summary-period">{e(item.get("period"))}</span>'
                f'<span class="summary-item-title">{e(item.get("title"))}</span>'
                f'{organization_html}'
                '</li>'
            )
        return '<ul class="summary-list">' + "".join(rows) + "</ul>"

    publication_rows = []
    for work in selected_works:
        ids = work.get("external_ids") or {}
        doi = ids.get("doi") or {}
        doi_value = str(doi.get("value") or "")
        doi_url = str(doi.get("url") or (f"https://doi.org/{doi_value}" if doi_value else ""))
        doi_html = (
            f'<a class="publication-doi" href="{e(doi_url)}">DOI: {e(doi_value)}</a>' if doi_value else ""
        )
        year = str((work.get("date") or {}).get("year") or "")
        venue = " · ".join(part for part in (str(work.get("journal") or ""), year) if part)
        publication_rows.append(
            '<li>'
            f'<span class="publication-authors">{summary_author_markup(work)}</span> '
            f'<span class="publication-title">{e(work.get("title"))}</span>'
            f'<div class="publication-meta">{e(venue)}{doi_html}</div>'
            '</li>'
        )

    email_links = ", ".join(
        f'<a href="mailto:{e(email)}">{e(email)}</a>' for email in profile.get("contact", {}).get("emails", [])
    )
    focus = " · ".join(e(item) for item in cv.get("focus", []))

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(cv.get('name'))} — One-page CV</title>
  <link rel="stylesheet" href="../assets/summary.css">
</head>
<body>
  <main class="summary-page">
    <header class="summary-header">
      <h1>{e(cv.get('name'))}</h1>
      <p class="summary-role">{e(cv.get('role'))}</p>
      <p class="summary-affiliation">{e(cv.get('affiliation'))}</p>
      <p class="summary-contact">
        <span>{email_links}</span>
        <span><a href="{e(profile.get('links', {}).get('orcid'))}">ORCID {e(profile.get('orcid_id'))}</a></span>
        <span><a href="{e(profile.get('links', {}).get('google_scholar'))}">Google Scholar</a></span>
      </p>
    </header>

    <section class="summary-intro">
      <p class="bio">{e(cv.get('bio'))}</p>
      <p class="interests"><strong>Research interests:</strong> {focus}</p>
    </section>

    <div class="summary-columns">
      <section class="summary-section">
        <h2>Appointments &amp; Training</h2>
        {compact_items(experience)}
      </section>
      <section class="summary-section">
        <h2>Education</h2>
        {compact_items(cv.get('education', []))}
        <div class="summary-subsection">
          <h2>Certification &amp; Licensure</h2>
          {compact_items(cv.get('licenses', []))}
        </div>
      </section>
    </div>

    <section class="summary-section summary-publications">
      <h2>Selected Publications</h2>
      <ol class="publication-list">{"".join(publication_rows)}</ol>
    </section>

    <footer class="summary-footer">Generated {generated.day} {generated.strftime('%B %Y')}</footer>
  </main>
</body>
</html>
"""


def render_publication_item(work: dict[str, Any], is_lead: bool, star_label: str = "") -> str:
    title = e(work.get("title"))
    url = e(work.get("url"))
    title_markup = f'<a href="{url}" target="_blank" rel="noopener">{title}</a>' if url else title
    authors = author_markup(work, is_lead, star_label)
    author_line = f'<p class="publication-authors">{authors}</p>' if authors else ""
    journal = e(work.get("journal"))
    year = e((work.get("date") or {}).get("year"))
    venue = " · ".join(part for part in (journal, year) if part)
    venue_line = f'<p class="publication-venue"><em>{venue}</em></p>' if venue else ""
    ids = work.get("external_ids") or {}
    meta = []
    doi = ids.get("doi") or {}
    if doi.get("value"):
        doi_url = e(doi.get("url") or f'https://doi.org/{doi["value"]}')
        meta.append(f'<a class="badge" href="{doi_url}" target="_blank" rel="noopener">DOI</a>')
    pmid = ids.get("pmid") or {}
    if pmid.get("value"):
        pmid_url = e(pmid.get("url") or f'https://pubmed.ncbi.nlm.nih.gov/{pmid["value"]}')
        meta.append(f'<a class="badge" href="{pmid_url}" target="_blank" rel="noopener">PubMed</a>')
    return f"""<li class="publication-item">
      <div>
        <h3 class="publication-title">{title_markup}</h3>
        {author_line}
        {venue_line}
        <div class="publication-meta">{''.join(meta)}</div>
      </div>
    </li>"""


def publication_section(works: list[dict[str, Any]], overrides: dict[str, Any], labels: dict[str, str]) -> str:
    lead_items = []
    co_items = []
    for work in works:
        lead = is_lead_work(work, overrides)
        put_code = str(work.get("put_code") or "")
        star_label = str((overrides.get(put_code) or {}).get("label") or "") if lead else ""
        markup = render_publication_item(work, lead, star_label)
        (lead_items if lead else co_items).append(markup)

    lead_html = "".join(lead_items) or f'<li class="empty-state">—</li>'
    co_html = "".join(co_items) or f'<li class="empty-state">—</li>'

    return f"""<div class="pub-tabs">
      <button class="pub-tab is-active" type="button" data-pub-tab="lead" aria-pressed="true">{e(labels['publications_lead'])} ({len(lead_items)})</button>
      <button class="pub-tab" type="button" data-pub-tab="co" aria-pressed="false">{e(labels['publications_co'])} ({len(co_items)})</button>
    </div>
    <p class="lead-legend">{e(labels['lead_star_note'])}</p>
    <div class="pub-panel" data-pub-group="lead">
      <h3 class="pub-print-heading">{e(labels['publications_lead'])} ({len(lead_items)})</h3>
      <ul class="publication-list">{lead_html}</ul>
    </div>
    <div class="pub-panel" data-pub-group="co" hidden>
      <h3 class="pub-print-heading">{e(labels['publications_co'])} ({len(co_items)})</h3>
      <ul class="publication-list">{co_html}</ul>
    </div>"""


def project_list(items: list[dict[str, str]]) -> str:
    rows = []
    for item in items:
        detail = item.get("detail")
        detail_html = f'<p>{e(detail)}</p>' if detail else ""
        rows.append(
            f"""<li class="project-item">
              <span class="item-meta">{e(item.get('period'))} · {e(item.get('role'))}</span>
              <h3>{e(item.get('title'))}</h3>
              <p>{e(item.get('sponsor'))}</p>
              {detail_html}
            </li>"""
        )
    return '<ol class="project-list">' + "".join(rows) + "</ol>"


def award_list(items: list[dict[str, str]]) -> str:
    rows = []
    for item in items:
        detail = item.get("detail")
        detail_html = f'<p class="item-detail">{e_multiline(detail)}</p>' if detail else ""
        rows.append(
            f"""<li class="award-item">
              <span class="item-meta">{e(item.get('date'))}</span>
              <h3>{e(item.get('title'))}</h3>
              <p class="item-organization">{e(item.get('organization'))}</p>
              {detail_html}
            </li>"""
        )
    return '<ol class="award-list">' + "".join(rows) + "</ol>"


def presentation_list(items: list[dict[str, str]]) -> str:
    rows = []
    for item in items:
        dates = item.get("dates")
        dates_html = f'<p class="item-meta pres-dates">{e(dates)}</p>' if dates else ""
        rows.append(
            f"""<li class="presentation-item">
              <button class="disclosure-trigger" type="button" aria-expanded="false" data-disclosure>
                <span class="item-meta">{e(item.get('year'))} · {e(item.get('type'))}</span>
                <span class="item-venue-line">{e(item.get('venue'))}</span>
              </button>
              <div class="item-body" hidden>
                {dates_html}
                <p class="pres-title">{e(item.get('title'))}</p>
              </div>
            </li>"""
        )
    return '<ol class="presentation-list">' + "".join(rows) + "</ol>"


def build_page(profile: dict[str, Any], cv: dict[str, Any], orcid: dict[str, Any], overrides: dict[str, Any]) -> str:
    lang = cv["lang"]
    labels = cv["labels"]
    is_ko = lang == "ko"
    prefix = "" if is_ko else "../"
    language_href = "en/" if is_ko else "../"
    pdf_name = f"{PDF_SLUG}-{lang}.pdf"
    works = orcid.get("works") or []
    address = profile["contact"]["address_ko" if is_ko else "address_en"]
    sync_date = str(orcid.get("last_synced_utc") or "").split("T")[0]
    generated = build_date()
    generated_iso = generated.strftime("%Y-%m-%d")
    pdf_download_name = pdf_name.replace(".pdf", f"-{generated_iso}.pdf")
    summary_pdf_download_name = SUMMARY_PDF_NAME.replace(".pdf", f"-{generated_iso}.pdf")
    generated_text = (
        f"작성일 {generated.year}년 {generated.month}월 {generated.day}일"
        if is_ko
        else f"Generated {generated.day} {generated.strftime('%B %Y')}"
    )
    email_links = "<br>".join(
        f'<a href="mailto:{e(email)}">{e(email)}</a>' for email in profile["contact"].get("emails", [])
    )
    summary_download_link = (
        f'<span aria-hidden="true"> · </span><a class="cv-link" href="{prefix}downloads/{SUMMARY_PDF_NAME}" '
        f'download="{e(summary_pdf_download_name)}">{e(labels["download_summary_pdf"])} ↓</a>'
        if not is_ko
        else ""
    )
    research_label = "연구 분야" if is_ko else "Research interests"
    focus = " · ".join(e(item) for item in cv.get("focus", []))
    show_photo = profile.get("site", {}).get("show_photo", True)
    portrait = (
        f'<div class="portrait-wrap"><img class="portrait" src="{prefix}{e(profile["photo"])}" '
        f'alt="{e(cv["name"])}" width="434" height="530"></div>'
        if show_photo
        else ""
    )
    json_ld = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": cv["name"],
        "alternateName": cv["name_secondary"],
        "jobTitle": cv["role"],
        "affiliation": {"@type": "Hospital", "name": cv["affiliation"]},
        "identifier": profile["orcid_id"],
        "sameAs": [profile["links"]["orcid"], profile["links"]["google_scholar"]],
        "knowsAbout": cv.get("focus", []),
    }
    description = cv["bio"]
    page_title = f'{cv["name"]} — {cv["role"]}'
    publications_total = e(labels["publications_total"].replace("{count}", str(len(works))))
    publications_markup = publication_section(works, overrides, labels)

    licenses_panel = (
        f'<div class="panel" style="margin-top: 28px"><h3 class="card-title">{e(labels["licenses"])}</h3>{clean_list(cv["licenses"])}</div>'
        if cv.get("licenses")
        else ""
    )
    presentations_panel = (
        f'<div class="panel" style="margin-top: 36px"><h3 class="card-title">{e(labels["presentations"])}</h3>{presentation_list(cv["presentations"])}</div>'
        if cv.get("presentations")
        else ""
    )
    research_nav = f'<a href="#research">{e(labels["nav_research"])}</a>\n' if cv.get("projects") else ""
    research_section = (
        f"""<section id="research" class="section">
      <div class="section-heading"><div><p class="section-kicker">Research</p><h2>{e(labels['research'])}</h2></div></div>
      <div class="panel"><h3 class="card-title">{e(labels['research'])}</h3>{project_list(cv['projects'])}</div>
    </section>"""
        if cv.get("projects")
        else ""
    )

    base_url = str(profile.get("site", {}).get("base_url") or "").rstrip("/")
    canonical_path = "/" if is_ko else "/en/"
    canonical_url = f"{base_url}{canonical_path}" if base_url else ""
    canonical_tag = f'<link rel="canonical" href="{e(canonical_url)}">' if canonical_url else ""
    og_url_tag = f'<meta property="og:url" content="{e(canonical_url)}">' if canonical_url else ""
    hreflang_tags = ""
    if base_url:
        hreflang_tags = (
            f'<link rel="alternate" hreflang="ko" href="{e(base_url)}/">'
            f'<link rel="alternate" hreflang="en" href="{e(base_url)}/en/">'
            f'<link rel="alternate" hreflang="x-default" href="{e(base_url)}/">'
        )
    og_image = f"{base_url}/{e(profile['photo'])}" if base_url else f"{prefix}{e(profile['photo'])}"
    favicon_color = str(profile["site"]["theme_color"]).replace("#", "%23")
    favicon_svg = (
        "data:image/svg+xml,"
        "<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 32 32'>"
        f"<rect width='32' height='32' rx='7' fill='{favicon_color}'/>"
        "<text x='16' y='23' font-family='Georgia,serif' font-size='18' "
        "font-weight='700' fill='%23fff' text-anchor='middle'>" + BRAND[0] + "</text></svg>"
    )

    return f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{e(description)}">
  <meta name="theme-color" content="{e(profile['site']['theme_color'])}">
  <link rel="icon" href="{favicon_svg}">
  <meta property="og:type" content="profile">
  <meta property="og:title" content="{e(page_title)}">
  <meta property="og:description" content="{e(description)}">
  <meta property="og:image" content="{og_image}">
  {og_url_tag}
  {canonical_tag}
  {hreflang_tags}
  <title>{e(page_title)}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&family=Noto+Serif+KR:wght@400;700&display=swap">
  <link rel="stylesheet" href="{prefix}assets/site.css">
  <script type="application/ld+json">{json.dumps(json_ld, ensure_ascii=False).replace('</', '<\\/')}</script>
</head>
<body class="lang-{lang}">
  <a class="skip-link" href="#main">{e(labels['skip'])}</a>
  <header class="site-header">
    <div class="header-inner">
      <a class="brand" href="{prefix}">{e(BRAND)}</a>
      <div class="nav-wrap">
        <nav class="main-nav" aria-label="Primary">
          <a href="#about">{e(labels['nav_about'])}</a>
          <a href="#experience">{e(labels['nav_experience'])}</a>
          <a href="#publications">{e(labels['nav_publications'])}</a>
          {research_nav}          <a href="#awards">{e(labels['nav_awards'])}</a>
        </nav>
        <div class="header-actions">
          <a class="header-link language-link" href="{language_href}" hreflang="{'en' if is_ko else 'ko'}">{e(labels['language'])}</a>
          <a class="header-link" href="{prefix}downloads/{pdf_name}" download="{e(pdf_download_name)}">CV PDF</a>
        </div>
      </div>
    </div>
  </header>

  <main id="main" class="page-shell">
    <div class="academic-layout">
      <aside class="author-profile" aria-label="{e(labels['contact'])}">
        {portrait}
        <h1 id="hero-title">{e(cv['name'])}</h1>
        <p class="author-name-secondary">{e(cv['name_secondary'])}</p>
        <p class="author-role">{e(cv['role'])}</p>
        <p class="author-affiliation">{e(cv['affiliation'])}</p>
        <p class="author-tagline">{e(cv['tagline'])}</p>
        <dl class="author-contact">
          <div><dt>{e(labels['email'])}</dt><dd>{email_links}</dd></div>
          <div><dt>{e(labels['orcid'])}</dt><dd><a href="{e(profile['links']['orcid'])}" target="_blank" rel="me noopener">{e(profile['orcid_id'])}</a></dd></div>
          <div><dt>{e(labels['scholar'])}</dt><dd><a href="{e(profile['links']['google_scholar'])}" target="_blank" rel="noopener">Google Scholar</a></dd></div>
        </dl>
        <div class="cv-downloads"><a class="cv-link" href="{prefix}downloads/{pdf_name}" download="{e(pdf_download_name)}">{e(labels['download_pdf'])} ↓</a>{summary_download_link}</div>
        <p class="print-date"><time datetime="{generated_iso}">{e(generated_text)}</time></p>
      </aside>

      <div class="academic-content">
        <section id="about" class="section intro-section">
          <h2>{e(labels['about'])}</h2>
          <p class="intro-bio">{e(cv['bio'])}</p>
          <p class="research-interests"><strong>{research_label}</strong><span>{focus}</span></p>
          <p class="address-line">{e(address)}</p>
        </section>

    <section id="experience" class="section">
      <div class="section-heading"><div><p class="section-kicker">Curriculum Vitae</p><h2>{e(labels['experience'])}</h2></div></div>
      <div class="career-grid">
        <div class="panel"><h3 class="card-title">{e(labels['experience'])}</h3>{timeline(cv.get('experience', []))}</div>
        <div>
          <div class="panel"><h3 class="card-title">{e(labels['education'])}</h3>{timeline(cv.get('education', []))}</div>
          {licenses_panel}
        </div>
      </div>
    </section>

    <section id="publications" class="section">
      <div class="section-heading">
        <div><p class="section-kicker">ORCID · {e(profile['orcid_id'])}</p><h2>{e(labels['publications'])}</h2></div>
        <p>{publications_total} · {e(labels['publications_note'])}</p>
      </div>
      <div class="publication-head"><span class="sync-note">{e(labels['last_synced'])}: {e(sync_date)}</span></div>
      {publications_markup}
    </section>

    {research_section}

    <section id="awards" class="section">
      <div class="section-heading"><div><p class="section-kicker">Recognition</p><h2>{e(labels['awards'])}</h2></div></div>
      <div class="panel"><h3 class="card-title">{e(labels['awards'])}</h3>{award_list(cv.get('awards', []))}</div>
      {presentations_panel}
    </section>
      </div>
    </div>
  </main>

  <footer class="site-footer">
    <div class="footer-inner"><p>© <span data-current-year></span> {e(cv['name'])}</p><p>{e(labels['last_synced'])}: {e(sync_date)}</p></div>
  </footer>
  <script src="{prefix}assets/site.js"></script>
</body>
</html>
"""


def main() -> int:
    required = [
        CONTENT / "profile.json",
        CONTENT / "cv.ko.json",
        CONTENT / "cv.en.json",
        CONTENT / "cv.summary.en.json",
        DATA / "orcid.json",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required files: {', '.join(missing)}")

    profile = load_json(CONTENT / "profile.json")
    orcid = load_json(DATA / "orcid.json")
    if profile["orcid_id"] != orcid["orcid_id"]:
        raise ValueError("The ORCID ID in content/profile.json does not match data/orcid.json")
    if not orcid.get("works"):
        raise ValueError("ORCID snapshot contains no works; refusing to build an empty publications page")

    overrides_path = CONTENT / "publication_overrides.json"
    overrides = load_json(overrides_path) if overrides_path.exists() else {}

    resolved_dist = DIST.resolve()
    if resolved_dist.parent != ROOT.resolve() or resolved_dist.name != "dist":
        raise RuntimeError(f"Unsafe output directory: {resolved_dist}")
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    shutil.copytree(ASSETS, DIST / "assets")
    shutil.copytree(DATA, DIST / "data")
    (DIST / "downloads").mkdir()
    (DIST / "en").mkdir()

    ko = load_json(CONTENT / "cv.ko.json")
    en = load_json(CONTENT / "cv.en.json")
    summary_en = load_json(CONTENT / "cv.summary.en.json")
    (DIST / "index.html").write_text(build_page(profile, ko, orcid, overrides), encoding="utf-8")
    (DIST / "en" / "index.html").write_text(build_page(profile, en, orcid, overrides), encoding="utf-8")
    PREVIEW.mkdir(parents=True, exist_ok=True)
    (PREVIEW / "summary-en.html").write_text(
        build_summary_page(profile, en, orcid, overrides, summary_en), encoding="utf-8"
    )
    (DIST / ".nojekyll").write_text("", encoding="utf-8")

    base_url = str(profile.get("site", {}).get("base_url") or "").rstrip("/")
    robots_lines = ["User-agent: *", "Allow: /"]
    if base_url:
        robots_lines.append(f"Sitemap: {base_url}/sitemap.xml")
        lastmod = str(orcid.get("last_synced_utc") or "").split("T")[0]
        sitemap_urls = [f"{base_url}/", f"{base_url}/en/"]
        sitemap_entries = "".join(
            f"  <url><loc>{html.escape(url)}</loc><lastmod>{lastmod}</lastmod></url>\n" for url in sitemap_urls
        )
        sitemap = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{sitemap_entries}"
            "</urlset>\n"
        )
        (DIST / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (DIST / "robots.txt").write_text("\n".join(robots_lines) + "\n", encoding="utf-8")
    print(f"Built Korean and English pages in {DIST.relative_to(ROOT)} and English summary print source")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
