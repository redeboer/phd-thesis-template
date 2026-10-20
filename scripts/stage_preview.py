"""Assemble the template's two live examples for the existing Pages upload."""

# ruff: file-ignore[suspicious-subprocess-import, subprocess-without-shell-equals-true, start-process-with-partial-path]

import os
import re
import shutil
import subprocess
from pathlib import Path

REPOSITORY = "redeboer/phd-thesis-template"
SITE_URL = "https://redeboer.github.io/phd-thesis-template/"
CALLOUT = '<p class="alert alert-info" id="rub-preview">Also available: <a href="rub/">RUB theme preview</a>.</p>'


def main() -> None:
    if os.environ.get("GITHUB_REPOSITORY") != REPOSITORY:
        return
    site_url = SITE_URL
    if match := re.fullmatch(
        r"refs/pull/(\d+)/merge", os.environ.get("GITHUB_REF", "")
    ):
        site_url = (
            f"https://redeboer.github.io/phd-thesis-template-preview/pr-{match[1]}/"
        )
    for task in ("rub-paperback", "rub-hardcover"):
        subprocess.run(["pixi", "run", task], check=True)
    output = Path("docs/_build")
    render_html(site_url)
    for directory, stem in (("html", "thesis"), ("rub", "thesis-rub")):
        for name in (
            "index.html",
            f"{stem}.pdf",
            f"{stem}.epub",
            "thesis-paperback.pdf",
            "thesis-hardcover.pdf",
        ):
            path = output / directory / name
            if not path.is_file():
                message = f"Missing preview output: {path}"
                raise FileNotFoundError(message)
    destination = output / "html" / "rub"
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(output / "rub", destination)
    index = output / "html" / "index.html"
    html = index.read_text(encoding="utf-8")
    if 'id="rub-preview"' not in html:
        marker = '<main class="content" id="quarto-document-content">'
        if html.count(marker) != 1:
            message = "Cannot locate the main content of the general landing page"
            raise RuntimeError(message)
        index.write_text(
            html.replace(marker, marker + "\n" + CALLOUT, 1), encoding="utf-8"
        )
    write_summary(site_url)


def write_summary(site_url: str) -> None:
    if site_url != SITE_URL and (summary := os.environ.get("GITHUB_STEP_SUMMARY")):
        with Path(summary).open("a", encoding="utf-8") as stream:
            stream.write(
                "> [!TIP]\n"
                f"> PR preview: [General theme]({site_url}) · [RUB theme]({site_url}rub/)."
            )


def render_html(site_url: str) -> None:
    profile = Path("docs/_quarto-preview.yml")
    with profile.open("x", encoding="utf-8") as stream:
        stream.write(f"book:\n  site-url: {site_url}\n")
    try:
        for theme, directory, suffix in (
            ("general", "html", ""),
            ("rub", "rub", "rub/"),
        ):
            if theme == "general" and site_url == SITE_URL:
                continue
            profile.write_text(
                f"book:\n  site-url: {site_url}{suffix}\n", encoding="utf-8"
            )
            subprocess.run(
                [
                    "uv",
                    "run",
                    "quarto",
                    "render",
                    "docs",
                    "--no-clean",
                    f"--profile={theme},preview",
                    f"--output-dir=_build/{directory}",
                    "--to=html",
                ],
                check=True,
            )
    finally:
        profile.unlink()


if __name__ == "__main__":
    raise SystemExit(main())
