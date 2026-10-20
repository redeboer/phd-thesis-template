"""Assemble the template's two live examples for the existing Pages upload."""

# ruff: file-ignore[suspicious-subprocess-import, subprocess-without-shell-equals-true, start-process-with-partial-path]

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

REPOSITORY = "redeboer/phd-thesis-template"
PREVIEW_URL = "https://redeboer.github.io/phd-thesis-template/rub/"
CALLOUT = '<p class="alert alert-info" id="rub-preview">Also available: <a href="rub/">RUB theme preview</a>.</p>'


def main() -> None:
    if os.environ.get("GITHUB_REPOSITORY") != REPOSITORY:
        return
    for task in ("rub-paperback", "rub-hardcover"):
        subprocess.run(["pixi", "run", task], check=True)
    output = Path("docs/_build")
    profile = Path("docs/_quarto-preview.yml")
    with profile.open("x", encoding="utf-8") as stream:
        stream.write(f"book:\n  site-url: {PREVIEW_URL}\n")
    try:
        subprocess.run(
            [
                "uv",
                "run",
                "quarto",
                "render",
                "docs",
                "--no-clean",
                "--profile=rub,preview",
                "--output-dir=_build/rub",
                "--to=html",
            ],
            check=True,
        )
    finally:
        profile.unlink()
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


if __name__ == "__main__":
    main()
