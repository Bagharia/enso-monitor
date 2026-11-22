"""Génère dossier.pdf à partir de dossier.md (Markdown + diagrammes Mermaid).

Usage : python3 build.py
Deux passes : la 1re repère la page de chaque section, la 2e écrit le sommaire avec ces numéros.
"""
import html
import re
import subprocess
from pathlib import Path

import markdown

HERE = Path(__file__).parent
CHROME = "google-chrome"


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def to_html(markdown_text: str, page_numbers: dict[str, int]) -> str:
    # Les blocs ```mermaid deviennent des <pre class="mermaid"> rendus par mermaid.js.
    def mermaid_block(match: re.Match) -> str:
        return f'<pre class="mermaid">{html.escape(match.group(1))}</pre>'

    source = re.sub(r"```mermaid\n(.*?)```", mermaid_block, markdown_text, flags=re.S)
    body = markdown.markdown(source, extensions=["tables", "fenced_code", "md_in_html"])

    # Sommaire : titres de niveau 1 (sections) et 2 (sous-sections)
    entries = []
    for level, title in re.findall(r"<h([12])>(.*?)</h\1>", body):
        plain = re.sub(r"<.*?>", "", title)
        anchor = slugify(plain)
        page = page_numbers.get(plain, "")
        css = "toc-1" if level == "1" else "toc-2"
        entries.append(
            f'<li class="{css}"><a href="#{anchor}">{plain}</a><span>{page}</span></li>'
        )
        body = body.replace(f"<h{level}>{title}</h{level}>",
                            f'<h{level} id="{anchor}">{title}</h{level}>', 1)
    body = body.replace("<!-- TOC -->", f'<ul class="toc-list">{"".join(entries)}</ul>')

    template = (HERE / "template.html").read_text(encoding="utf-8")
    return template.replace("{{BODY}}", body)


def render_pdf(html_text: str, output: Path) -> None:
    html_path = HERE / "dossier.html"
    html_path.write_text(html_text, encoding="utf-8")
    subprocess.run(
        [CHROME, "--headless=new", "--no-sandbox", "--disable-gpu",
         "--no-pdf-header-footer", "--virtual-time-budget=15000",
         f"--print-to-pdf={output}", html_path.as_uri()],
        check=True, capture_output=True,
    )


def find_heading_pages(pdf: Path, titles: list[str]) -> dict[str, int]:
    pages = subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                           capture_output=True, text=True, check=True).stdout.split("\f")
    found: dict[str, int] = {}
    for title in titles:
        for number, text in enumerate(pages, start=1):
            if number <= 2:  # couverture et sommaire
                continue
            if any(line.strip() == title for line in text.splitlines()):
                found[title] = number
                break
    return found


def main() -> None:
    markdown_text = (HERE / "dossier.md").read_text(encoding="utf-8")
    titles = [re.sub(r"[*`]", "", t) for t in re.findall(r"^#{1,2} (.+)$", markdown_text, re.M)]
    output = HERE / "dossier.pdf"
    render_pdf(to_html(markdown_text, {}), output)  # passe 1
    page_numbers = find_heading_pages(output, titles)
    render_pdf(to_html(markdown_text, page_numbers), output)  # passe 2
    missing = [t for t in titles if t not in page_numbers]
    page_count = subprocess.run(["pdfinfo", str(output)], capture_output=True, text=True).stdout
    print(re.search(r"Pages:\s+\d+", page_count).group(0), "| titres sans page :", missing)


if __name__ == "__main__":
    main()
