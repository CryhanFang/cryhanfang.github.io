from __future__ import annotations

import html
import re
import shutil
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"


def inline(text: str) -> str:
    """Render the small inline Markdown subset used by this homepage."""
    placeholders: list[str] = []

    def hold(value: str) -> str:
        placeholders.append(value)
        return f"\x00{len(placeholders) - 1}\x00"

    text = html.escape(text, quote=False)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: hold(
            f'<a href="{html.escape(html.unescape(m.group(2)), quote=True)}" '
            'target="_blank" rel="noopener">'
            f"{m.group(1)}</a>"
        ),
        text,
    )
    text = re.sub(r"`([^`]+)`", lambda m: hold(f"<code>{m.group(1)}</code>"), text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # A single trailing star is used for equal/corresponding author markers
    # throughout the publication list, so single-star emphasis is intentionally
    # not supported. Double stars above still render bold text.
    for index, value in enumerate(placeholders):
        text = text.replace(f"\x00{index}\x00", value)
    return text


def markdown(text: str) -> str:
    """Render headings, paragraphs, unordered lists, and inline formatting."""
    output: list[str] = []
    paragraph: list[str] = []
    in_list = False

    def close_paragraph() -> None:
        if paragraph:
            output.append(f"<p>{inline(' '.join(paragraph))}</p>")
            paragraph.clear()

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            output.append("</ul>")
            in_list = False

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            close_paragraph()
            close_list()
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", line)
        if heading:
            close_paragraph()
            close_list()
            level = len(heading.group(1))
            title = heading.group(2)
            section_id = ""
            if title.lower() == "publications":
                section_id = ' id="publication-list"'
            output.append(f"<h{level}{section_id}>{inline(title)}</h{level}>")
        elif line.startswith("- "):
            close_paragraph()
            if not in_list:
                output.append("<ul>")
                in_list = True
            output.append(f"<li>{inline(line[2:])}</li>")
        elif line.startswith("<!--") or line.endswith("-->"):
            continue
        else:
            close_list()
            paragraph.append(line)
    close_paragraph()
    close_list()
    return "\n".join(output)


def news(text: str) -> str:
    """Keep each news date and its complete body in the two grid columns."""
    rendered = markdown(text)
    return re.sub(
        r"<li>(<strong>[^<]+</strong>)\s*(.*?)</li>",
        r'<li>\1<span class="news-text">\2</span></li>',
        rendered,
    )


def publications(text: str) -> str:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    block_pattern = r"^:::selected\s*$\n(.*?)^:::\s*$"
    blocks = re.findall(block_pattern, text, flags=re.S | re.M)
    remaining = re.sub(block_pattern, "", text, flags=re.S | re.M)
    selected_html: list[str] = []
    link_names = ("paper", "project", "code", "dataset", "demo")

    for block in blocks:
        data: dict[str, str] = {}
        for line in block.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                data[key.strip().lower()] = value.strip()
        links = " · ".join(
            f'<a href="{html.escape(data[name], quote=True)}" target="_blank" '
            f'rel="noopener">{name.title()}</a>'
            for name in link_names
            if data.get(name)
        )
        selected_html.append(
            '<article class="paper">'
            '<div class="paper-image">'
            f'<span class="badge">{html.escape(data.get("venue", ""))}</span>'
            f'<img src="{html.escape(data.get("image", ""), quote=True)}" '
            f'alt="{html.escape(data.get("title", "Publication"), quote=True)} thumbnail">'
            '</div><div class="paper-text">'
            f'<h3>{html.escape(data.get("title", ""))}</h3>'
            f'<p>{inline(data.get("authors", ""))}</p>'
            f'<div class="paper-links">{links}</div>'
            '</div></article>'
        )

    marker = "# Publications"
    before, separator, after = remaining.partition(marker)
    if not separator:
        return markdown(remaining) + "\n" + "\n".join(selected_html)
    more_marker = "## Publications"
    selected_intro, more_separator, more = after.partition(more_marker)
    result = [markdown(before), "<h1>Publications</h1>"]
    if more_separator and selected_intro.strip():
        result.append(markdown(selected_intro))
    result.extend(selected_html)
    publication_list = more if more_separator else selected_intro
    if publication_list.strip():
        result.append(f'<div id="publication-list">{markdown(publication_list)}</div>')
    return "\n".join(filter(None, result))


def copy_existing_images() -> None:
    source = ROOT.parent / "cryhanfang.github.io-main" / "images"
    destination = ROOT / "assets" / "images"
    for name in ("profile.jpg", "TUNED.png", "clip2video.png", "project-mlfw.jpg"):
        target = destination / name
        candidate = source / name
        if not target.exists() and candidate.exists():
            shutil.copy2(candidate, target)


def main() -> None:
    copy_existing_images()
    template = (ROOT / "template.html").read_text(encoding="utf-8")
    replacements = {
        "{{ABOUT}}": markdown((CONTENT / "about.md").read_text(encoding="utf-8")),
        "{{NEWS}}": news((CONTENT / "news.md").read_text(encoding="utf-8")),
        "{{PUBLICATIONS}}": publications((CONTENT / "publications.md").read_text(encoding="utf-8")),
        "{{HONORS}}": markdown((CONTENT / "honors.md").read_text(encoding="utf-8")),
        "{{EDUCATION}}": markdown((CONTENT / "education.md").read_text(encoding="utf-8")),
        "{{YEAR}}": str(date.today().year),
    }
    for placeholder, rendered in replacements.items():
        template = template.replace(placeholder, rendered)
    (ROOT / "index.html").write_text(template, encoding="utf-8")
    print(f"Built {ROOT / 'index.html'}")


if __name__ == "__main__":
    main()
