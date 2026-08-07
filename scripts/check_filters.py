"""Regression checks for the thesis Lua filters."""

import re
from pathlib import Path

HTML_PATH = Path("docs/_build/html/chapters/background.html")
LATEX_PATH = Path("docs/thesis.tex")


def main() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    latex = LATEX_PATH.read_text(encoding="utf-8")
    html_reference = re.compile(r"Equation&nbsp;\(<span>[0-9.]+</span>\)</a>")
    if not html_reference.search(html):
        message = "HTML equation reference is not parenthesized once"
        raise FilterRegressionError(message)
    if "Equation&nbsp;((" in html:
        message = "HTML equation reference has duplicate parentheses"
        raise FilterRegressionError(message)
    if R"\eqref{eq-mass-energy}" not in latex:
        message = "LaTeX equation reference does not use \\eqref"
        raise FilterRegressionError(message)


class FilterRegressionError(RuntimeError):
    """Indicate that rendered filter output did not match expectations."""


if __name__ == "__main__":
    raise SystemExit(main())
