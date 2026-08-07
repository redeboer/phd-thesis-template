#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=14.0",
#     "typer>=0.16",
# ]
# ///
"""Configure a fresh checkout of the thesis template."""

# cspell:ignore Boer keepends licence Remco

from __future__ import annotations

import json
import re
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date as calendar_date
from enum import StrEnum
from pathlib import Path
from textwrap import dedent, indent
from typing import Annotated

import typer
from rich.console import Console
from rich.prompt import Prompt

CONSOLE = Console()
ERROR_CONSOLE = Console(stderr=True)
RUB_CONDITIONALS = 2
"""Number of ``rub-theme`` conditionals in ``docs/preamble/before-body.tex``."""
TEMPLATE_AUTHOR = "Remco de Boer"
"""Author in the copyright line of ``LICENSE`` of the pristine template."""
TEMPLATE_REPOSITORY = "redeboer/phd-thesis-template"
"""GitHub repository that the pristine template links to and is published from."""
TEMPLATE_INDEX_HEADING = "# About this template {.unnumbered}"
"""Heading of the landing page of the pristine template, ``docs/index.qmd``."""
THESIS_INDEX = """\
# Preface {.unnumbered}

Address the reader before the thesis proper begins: describe the context in which
the work was carried out, the intended audience, and any reading guidance. This page
is the landing page of the thesis website and the first page of the PDF, so keep it
short or replace it with a short summary of the thesis.
"""
"""Landing page written by :func:`configure_index` for a bootstrapped thesis."""


def bootstrap(  # ruff: ignore[too-many-arguments, too-many-positional-arguments]
    profile: Annotated[
        Profile | None, typer.Option(help="Template profile to configure.")
    ] = None,
    title: str | None = None,
    subtitle: str | None = None,
    given_name: str | None = None,
    family_name: str | None = None,
    institution: str | None = None,
    department: str | None = None,
    city: str | None = None,
    country: str | None = None,
    orcid: str | None = None,
    date: str | None = None,
    repository: Annotated[
        str | None, typer.Option(help="GitHub repository as OWNER/NAME.")
    ] = None,
    degree: Annotated[
        str | None, typer.Option(help="Degree used by the general profile.")
    ] = None,
    rub_degree: Annotated[
        str | None, typer.Option(help="Degree used by the RUB profile.")
    ] = None,
    supervisor: Annotated[
        str | None, typer.Option(help="Supervisor used by the general profile.")
    ] = None,
    examiner: Annotated[
        str | None, typer.Option(help="Examiner used by the general profile.")
    ] = None,
    defence_date: str | None = None,
    faculty: Annotated[
        str | None, typer.Option(help="Faculty used by the RUB profile.")
    ] = None,
    first_examiner: Annotated[
        str | None, typer.Option(help="First examiner used by the RUB profile.")
    ] = None,
    second_examiner: Annotated[
        str | None, typer.Option(help="Second examiner used by the RUB profile.")
    ] = None,
    root: Annotated[Path | None, typer.Option(hidden=True)] = None,
) -> None:
    """Configure a fresh checkout for the general or RUB thesis profile."""
    try:
        answers = collect_answers(
            profile=profile,
            title=title,
            subtitle=subtitle,
            given_name=given_name,
            family_name=family_name,
            institution=institution,
            department=department,
            city=city,
            country=country,
            orcid=orcid,
            date=date,
            repository=repository,
            degree=degree,
            rub_degree=rub_degree,
            supervisor=supervisor,
            examiner=examiner,
            defence_date=defence_date,
            faculty=faculty,
            first_examiner=first_examiner,
            second_examiner=second_examiner,
        )
        apply_answers(root or Path.cwd(), answers)
    except (RuntimeError, ValueError) as error:
        ERROR_CONSOLE.print(f"[bold red]Error:[/] {error}")
        raise typer.Exit(code=2) from None
    CONSOLE.print(
        f"[bold green]Configured the {answers.profile.value} thesis profile.[/] Review the changes with [bold]git diff[/bold]."
    )


def collect_answers(  # ruff: ignore[too-many-arguments]
    *,
    profile: Profile | None,
    title: str | None,
    subtitle: str | None,
    given_name: str | None,
    family_name: str | None,
    institution: str | None,
    department: str | None,
    city: str | None,
    country: str | None,
    orcid: str | None,
    date: str | None,
    repository: str | None,
    degree: str | None,
    rub_degree: str | None,
    supervisor: str | None,
    examiner: str | None,
    defence_date: str | None,
    faculty: str | None,
    first_examiner: str | None,
    second_examiner: str | None,
) -> Answers:
    """Collect and validate interactive or command-line answers."""
    if profile is None:
        profile = Profile(
            Prompt.ask(
                prompt="Profile",
                choices=[item.value for item in Profile],
                default=Profile.GENERAL.value,
                console=CONSOLE,
            )
        )
    rub = profile is Profile.RUB
    repository = ask(
        repository,
        prompt="GitHub repository (OWNER/NAME)",
        validator=validate_repository,
    )
    rub_degree_value = (
        ask(rub_degree, prompt="RUB degree", default="Doktors der Naturwissenschaften")
        if rub
        else None
    )
    faculty_value = (
        ask(faculty, prompt="RUB faculty", default="Fakultät für Physik und Astronomie")
        if rub
        else None
    )
    first_examiner_value = ask(first_examiner, prompt="First examiner") if rub else None
    second_examiner_value = (
        ask(second_examiner, prompt="Second examiner") if rub else None
    )
    return Answers(
        profile=profile,
        title=ask(title, prompt="Thesis title"),
        subtitle=ask_optional(subtitle, prompt="Thesis subtitle (optional)"),
        given_name=ask(given_name, prompt="Author given name"),
        family_name=ask(family_name, prompt="Author family name"),
        institution=ask(
            institution,
            prompt="Institution",
            default="Ruhr University Bochum" if rub else None,
        ),
        department=ask(
            department, prompt="Department", default="Physics" if rub else None
        ),
        city=ask(city, prompt="City", default="Bochum" if rub else None),
        country=ask(country, prompt="Country", default="Germany" if rub else None),
        orcid=ask_optional(orcid, prompt="ORCID (optional)", validator=validate_orcid),
        date=ask(
            date,
            prompt="Thesis date",
            default="today",
            validator=lambda value: validate_date(value, allow_today=True),
        ),
        repository=repository,
        degree=rub_degree_value
        or ask(degree, prompt="Degree", default="Doctor of Philosophy"),
        supervisor=first_examiner_value or ask(supervisor, prompt="Supervisor"),
        examiner=second_examiner_value or ask(examiner, prompt="Examiner"),
        defence_date=ask(
            defence_date,
            prompt="Defence date",
            default="TBA",
            validator=lambda value: validate_date(value, allow_tba=True),
        ),
        rub_degree=rub_degree_value,
        faculty=faculty_value,
        first_examiner=first_examiner_value,
        second_examiner=second_examiner_value,
    )


def apply_answers(root: Path, answers: Answers) -> None:
    """Write the selected profile configuration."""
    root = root.resolve()
    docs = root / "docs"
    main_path = docs / "_quarto.yml"
    main_text = configure_main(main_path, answers)
    task_path = root / "pixi.toml"
    task_text = task_path.read_text(encoding="utf-8")
    if answers.profile is Profile.RUB:
        rub_path = docs / "_quarto-rub.yml"
        configure_rub(rub_path, answers)
        main_text = apply_rub_configuration(main_text, main_path, answers)
        rub_path.unlink()
        (docs / "favicon.ico").unlink()
    else:
        main_text = apply_general_configuration(main_text, main_path)
        remove_rub_spelling_configuration(root)
        remove_rub_hook_exclude(root / ".pre-commit-config.yaml")
        remove_rub_files(docs)
    resolve_rub_branches(
        docs / "preamble" / "before-body.tex",
        keep_rub=answers.profile is Profile.RUB,
    )
    configure_index(docs / "index.qmd")
    configure_documentation(root / "README.md", answers.profile)
    configure_license(root / "LICENSE", answers)
    task_text = remove_rub_tasks(task_text, task_path)
    task_text = remove_template_tasks(task_text, task_path)
    task_path.write_text(task_text, encoding="utf-8")
    main_path.write_text(main_text, encoding="utf-8")
    (docs / "_quarto-general.yml").unlink()
    remove_template_files(root)


def ask(
    current: str | None,
    /,
    prompt: str,
    *,
    default: str | None = None,
    validator: Validator | None = None,
) -> str:
    """Validate a CLI value or keep prompting for an interactive value."""
    interactive = current is None
    while True:
        response = (
            Prompt.ask(prompt, default=default, console=CONSOLE)
            if interactive
            else current
        )
        value = "" if response is None else response.strip()
        error = None if value else f"A value is required for {prompt.lower()}"
        if error is None and validator is not None:
            error = validator(value)
        if error is None:
            return value
        if not interactive:
            raise ValueError(error)
        ERROR_CONSOLE.print(f"[bold red]Invalid value:[/] {error}")


def ask_optional(
    current: str | None, /, prompt: str, *, validator: Validator | None = None
) -> str:
    """Validate an optional CLI value or keep prompting for an interactive value."""
    interactive = current is None
    while True:
        response = (
            Prompt.ask(prompt, default="", show_default=False, console=CONSOLE)
            if interactive
            else current
        )
        value = "" if response is None else response.strip()
        error = validator(value) if value and validator is not None else None
        if error is None:
            return value
        if not interactive:
            raise ValueError(error)
        ERROR_CONSOLE.print(f"[bold red]Invalid value:[/] {error}")


def validate_repository(value: str) -> str | None:
    """Validate a GitHub OWNER/REPOSITORY identifier."""
    owner, separator, repository = value.partition("/")
    valid_owner = re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", owner)
    valid_repository = re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", repository)
    if separator and valid_owner and valid_repository:
        return None
    return "Use the GitHub form OWNER/REPOSITORY (for example, redeboer/my-thesis)"


def validate_orcid(value: str) -> str | None:
    """Validate the shape of an ORCID identifier."""
    if re.fullmatch(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]", value):
        return None
    return "Use the ORCID form 0000-0000-0000-0000"


def validate_date(
    value: str, *, allow_today: bool = False, allow_tba: bool = False
) -> str | None:
    """Validate an ISO calendar date or an explicitly allowed placeholder."""
    if allow_today and value == "today":
        return None
    if allow_tba and value == "TBA":
        return None
    try:
        calendar_date.fromisoformat(value)
    except ValueError:
        return "Use an ISO date in YYYY-MM-DD format"
    return None


def configure_main(path: Path, answers: Answers) -> str:
    """Return shared thesis metadata with placeholders replaced."""
    text = path.read_text(encoding="utf-8")
    template_owner, template_name = TEMPLATE_REPOSITORY.split("/", maxsplit=1)
    owner, name = answers.repository.split("/", maxsplit=1)
    subtitle = (
        indent(
            dedent(f"""\
          title: {yaml_string(answers.title)}
          subtitle: {yaml_string(answers.subtitle)}
        """),
            "  ",
        )
        if answers.subtitle
        else indent(
            dedent(f"""\
          title: {yaml_string(answers.title)}
        """),
            "  ",
        )
    )
    orcid = (
        indent(
            dedent(f"""\
              country: *country
          orcid: {answers.orcid}
        """),
            "      ",
        )
        if answers.orcid
        else """          country: *country
"""
    )
    replacements = {
        "degree: Doctor of Philosophy": f"degree: {yaml_string(answers.degree)}",
        "institution: &institution Your University": f"institution: &institution {yaml_string(answers.institution)}",
        "department: &department Your Department": f"department: &department {yaml_string(answers.department)}",
        "city: &city Your City": f"city: &city {yaml_string(answers.city)}",
        "country: &country Your Country": f"country: &country {yaml_string(answers.country)}",
        "supervisor: Prof. Supervisor Name": f"supervisor: {yaml_string(answers.supervisor)}",
        "examiner: Prof. Examiner Name": f"examiner: {yaml_string(answers.examiner)}",
        "defence-date: TBA": f"defence-date: {yaml_string(answers.defence_date)}",
        indent(
            dedent("""\
          title: "Your Thesis Title"
          subtitle: "A concise description of your research"
        """),
            "  ",
        ): subtitle,
        "given: Your": f"given: {yaml_string(answers.given_name)}",
        "family: Name": f"family: {yaml_string(answers.family_name)}",
        indent(
            dedent("""\
              country: *country
          orcid: 0000-0000-0000-0000
        """),
            "      ",
        ): orcid,
        "date: today": f"date: {yaml_string(answers.date)}",
        f"https://github.com/{TEMPLATE_REPOSITORY}": f"https://github.com/{answers.repository}",
        f"https://{template_owner}.github.io/{template_name}": f"https://{owner}.github.io/{name}",
    }
    for old, new in replacements.items():
        text = replace_once(text, old, new, path)
    return text


def apply_general_configuration(text: str, path: Path) -> str:
    """Inline the general profile and drop the profile group from the main config."""
    replacements = {
        dedent("""\
        profile:
          group:
            - [general, rub]

        """): "",
        indent(
            dedent("""\
          output-file: thesis
          page-navigation: true
        """),
            "  ",
        ): indent(
            dedent("""\
          output-file: thesis
          navbar:
            collapse: false
            right:
              - icon: download
                menu:
                  - href: thesis.pdf
                    text: PDF
                    icon: file-pdf
                  - href: thesis.epub
                    text: ePub
                    icon: tablet
                  - href: thesis-paperback.pdf
                    text: PDF (paperback)
                    icon: file-pdf-fill
                  - href: thesis-hardcover.pdf
                    text: PDF (hardcover)
                    icon: file-pdf-fill
          page-navigation: true
        """),
            "  ",
        ),
    }
    for old, new in replacements.items():
        text = replace_once(text, old, new, path)
    return text


def apply_rub_configuration(text: str, path: Path, answers: Answers) -> str:
    """Make the RUB configuration the repository's main Quarto configuration."""
    rub = require_rub_answers(answers)
    replacements = {
        dedent("""\
        profile:
          group:
            - [general, rub]

        """): "",
        dedent(f"""\
        thesis:
          degree: {yaml_string(answers.degree)}
          institution: &institution {yaml_string(answers.institution)}
          department: &department {yaml_string(answers.department)}
          city: &city {yaml_string(answers.city)}
          country: &country {yaml_string(answers.country)}
          supervisor: {yaml_string(answers.supervisor)}
          examiner: {yaml_string(answers.examiner)}
          defence-date: {yaml_string(answers.defence_date)}
        """): dedent(f"""\
        thesis:
          degree: {yaml_string(rub.degree)}
          faculty: {yaml_string(rub.faculty)}
          first-examiner: {yaml_string(rub.first_examiner)}
          second-examiner: {yaml_string(rub.second_examiner)}
          institution: &institution {yaml_string(answers.institution)}
          department: &department {yaml_string(answers.department)}
          city: &city {yaml_string(answers.city)}
          country: &country {yaml_string(answers.country)}
          defence-date: {yaml_string(answers.defence_date)}
        """),
        indent(
            dedent("""\
          description: PhD thesis
          favicon: favicon.ico
          chapters:
        """),
            "  ",
        ): indent(
            dedent("""\
          description: PhD thesis, Ruhr University Bochum
          favicon: themes/rub/images/favicon.ico
          chapters:
        """),
            "  ",
        ),
        indent(
            dedent("""\
          output-file: thesis
          page-navigation: true
        """),
            "  ",
        ): indent(
            dedent("""\
          output-file: thesis-rub
          navbar:
            background: "#003560"
            collapse: false
            foreground: "#e7e7e7"
            logo: themes/rub/images/rub-white.svg
            right:
              - icon: download
                menu:
                  - href: thesis-rub.pdf
                    text: PDF
                    icon: file-pdf
                  - href: thesis-rub.epub
                    text: ePub
                    icon: tablet
                  - href: thesis-paperback.pdf
                    text: PDF (paperback)
                    icon: file-pdf-fill
                  - href: thesis-hardcover.pdf
                    text: PDF (hardcover)
                    icon: file-pdf-fill
          sidebar:
            logo: themes/rub/images/rub-text.svg
          page-navigation: true
        """),
            "  ",
        ),
        indent(
            dedent("""\
          html:
            theme:
        """),
            "  ",
        ): indent(
            dedent("""\
          html:
            css:
              - styles.css
              - themes/rub/styles.css
            theme:
        """),
            "  ",
        ),
        indent(
            dedent("""\
              css: styles.css
              toc: true
        """),
            "    ",
        ): indent(
            dedent("""\
              toc: true
        """),
            "    ",
        ),
        indent(
            dedent("""\
            include-in-header: preamble/configuration.tex
            include-before-body:
        """),
            "    ",
        ): indent(
            dedent("""\
            include-in-header:
              - preamble/configuration.tex
              - themes/rub/configuration.tex
            include-before-body:
        """),
            "    ",
        ),
    }
    for old, new in replacements.items():
        text = replace_once(text, old, new, path)
    return text


def configure_rub(path: Path, answers: Answers) -> str:
    """Return RUB metadata with placeholders replaced."""
    rub = require_rub_answers(answers)
    text = path.read_text(encoding="utf-8")
    replacements = {
        "degree: Doktors der Naturwissenschaften": f"degree: {yaml_string(rub.degree)}",
        "faculty: Fakultät für Physik und Astronomie": f"faculty: {yaml_string(rub.faculty)}",
        "first-examiner: Prof. Dr. First Examiner": f"first-examiner: {yaml_string(rub.first_examiner)}",
        "second-examiner: Prof. Dr. Second Examiner": f"second-examiner: {yaml_string(rub.second_examiner)}",
        "defence-date: TBA": f"defence-date: {yaml_string(answers.defence_date)}",
    }
    for old, new in replacements.items():
        text = replace_once(text, old, new, path)
    return text


def remove_rub_tasks(text: str, path: Path) -> str:
    """Remove the Pixi tasks that build the optional RUB variant.

    Both profiles drop these tasks: the RUB profile turns the standard tasks into
    RUB builds, and the general profile removes the RUB variant altogether.
    """
    text = remove_sequence_item(text, path, table="tasks.doc", item="rub")
    for task in ("rub", "rub-hardcover", "rub-paperback"):
        text = remove_pixi_task(text, path, task)
    return text


def resolve_rub_branches(path: Path, *, keep_rub: bool) -> None:
    """Resolve every ``rub-theme`` conditional in a Pandoc template to one branch.

    Only one profile survives bootstrapping, so the conditional has nothing left to
    choose between: the branch of the profile that was not selected is dead code.
    """
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    kept, depth, found = select_branches(lines, keep_rub=keep_rub)
    if depth != 0:
        message = f"Unbalanced rub-theme conditional in {path}"
        raise RuntimeError(message)
    if found != RUB_CONDITIONALS:
        message = (
            f"Expected {RUB_CONDITIONALS} rub-theme conditionals in {path}, "
            f"found {found}"
        )
        raise RuntimeError(message)
    path.write_text("".join(kept), encoding="utf-8")


def select_branches(lines: list[str], *, keep_rub: bool) -> tuple[list[str], int, int]:
    """Keep one branch per conditional, returning the lines, depth, and branch count.

    Pandoc templates nest conditionals, so this tracks ``$if(...)$`` depth instead of
    matching the first ``$else$`` or ``$endif$`` that follows a ``rub-theme`` branch.
    """
    kept: list[str] = []
    depth = 0
    keeping = True
    found = 0
    for line in lines:
        marker = line.strip()
        if depth == 0:
            if marker == "$if(rub-theme)$":
                depth = 1
                keeping = keep_rub
                found += 1
            else:
                kept.append(line)
            continue
        if marker.startswith("$if("):
            depth += 1
        elif marker == "$else$" and depth == 1:
            keeping = not keep_rub
            continue
        elif marker == "$endif$":
            depth -= 1
            if depth == 0:
                keeping = True
                continue
        if keeping:
            kept.append(line)
    return kept, depth, found


def configure_index(path: Path) -> None:
    """Replace the landing page about the template with a preface for the thesis.

    The pristine landing page explains what the template is to visitors of its
    published website. That explanation is meaningless in a bootstrapped thesis, so
    the whole page is rewritten instead of having its placeholders substituted.
    """
    text = path.read_text(encoding="utf-8")
    if TEMPLATE_INDEX_HEADING not in text:
        message = f"Expected the template landing page {TEMPLATE_INDEX_HEADING!r} in {path}. Has this repository already been bootstrapped?"
        raise RuntimeError(message)
    path.write_text(THESIS_INDEX, encoding="utf-8")


def configure_documentation(path: Path, profile: Profile) -> None:
    """Remove the README passages that describe the profile that was not selected."""
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "The one-shot bootstrap CLI configures either the general thesis or the RUB variant, then removes",
        "The one-shot bootstrap CLI configures the thesis, then removes",
        path,
    )
    text = replace_once(
        text,
        dedent("""\
        ## Optional RUB theme

        The template includes an optional [Ruhr University Bochum](https://www.ruhr-uni-bochum.de/en) [project profile](https://quarto.org/docs/projects/profiles.html). Selecting `rub` during bootstrap makes it the main configuration, so the standard Pixi tasks build the RUB thesis. The general profile uses a supervisor and examiner; the RUB title page instead uses first and second examiners.

        """),
        "## RUB branding\n\n" if profile is Profile.RUB else "",
        path,
    )
    if profile is not Profile.RUB:
        text = replace_once(
            text,
            dedent("""\
            > [!IMPORTANT]
            > The RUB name and logos are institutional branding governed by Ruhr University Bochum's [corporate-design guidance](https://services.ruhr-uni-bochum.de/de/corporate-design-der-ruhr-universitaet-bochum). Their inclusion in this template does not grant trademark rights or place those assets under the template's Apache licence.

            """),
            "",
            path,
        )
    path.write_text(text, encoding="utf-8")


def configure_license(path: Path, answers: Answers) -> None:
    """Put the thesis author in the copyright line of the license."""
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        TEMPLATE_AUTHOR,
        f"{answers.given_name} {answers.family_name}",
        path,
    )
    path.write_text(text, encoding="utf-8")


def remove_rub_spelling_configuration(root: Path) -> None:
    """Remove the spell-checker entries that only the RUB profile needs."""
    settings_path = root / ".cspell.json"
    settings_text = settings_path.read_text(encoding="utf-8")
    settings_text = replace_once(
        settings_text, '    "docs/themes/**/*.svg",\n', "", settings_path
    )
    settings_path.write_text(settings_text, encoding="utf-8")
    words_path = root / ".cspell" / "this-project.txt"
    words_text = words_path.read_text(encoding="utf-8")
    for word in ("Astronomie", "Doktors", "Fakultät", "Naturwissenschaften", "Physik"):
        words_text = replace_once(words_text, f"{word}\n", "", words_path)
    words_path.write_text(words_text, encoding="utf-8")


def remove_rub_hook_exclude(path: Path) -> None:
    """Remove the pre-commit exclude that only the RUB branding SVGs need."""
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        indent(
            dedent("""\
        - id: end-of-file-fixer
          exclude: >-
            (?x)^(
              .*/.*\\.svg$
            )$
        """),
            "      ",
        ),
        "      - id: end-of-file-fixer\n",
        path,
    )
    path.write_text(text, encoding="utf-8")


def remove_rub_files(docs: Path) -> None:
    """Remove the RUB profile configuration and its branding assets."""
    (docs / "_quarto-rub.yml").unlink()
    shutil.rmtree(docs / "themes")


def remove_pixi_task(text: str, path: Path, task: str) -> str:
    """Remove one template-only Pixi task."""
    pattern = re.compile(rf"\n\[tasks\.{task}\]\n.*?(?=\n\[)", re.DOTALL)
    matches = pattern.findall(text)
    if len(matches) != 1:
        message = (
            f"Expected one Pixi task named {task!r} in {path}, found {len(matches)}"
        )
        raise RuntimeError(message)
    return pattern.sub("", text, count=1)


def remove_sequence_item(text: str, path: Path, *, table: str, item: str) -> str:
    """Remove one item from a multiline Pixi sequence in a specific table."""
    table_pattern = re.compile(
        rf"(?P<header>\[{re.escape(table)}\]\n)"
        r"(?P<body>.*?)(?=\n\[|\Z)",
        re.DOTALL,
    )
    table_matches = list(table_pattern.finditer(text))
    if len(table_matches) != 1:
        message = (
            f"Expected one Pixi table {table!r} in {path}, found {len(table_matches)}"
        )
        raise RuntimeError(message)
    match = table_matches[0]
    item_line = f'    "{item}",\n'
    body = match.group("body")
    count = body.count(item_line)
    if count != 1:
        message = (
            f"Expected one sequence item {item!r} in Pixi table {table!r} "
            f"in {path}, found {count}"
        )
        raise RuntimeError(message)
    new_table = match.group("header") + body.replace(item_line, "", 1)
    return text[: match.start()] + new_table + text[match.end() :]


def remove_template_tasks(text: str, path: Path) -> str:
    """Remove Pixi tasks that only validate or configure the template."""
    text = replace_once(
        text,
        'description = "Build every supported thesis format and test the Lua filters"',
        'description = "Build every supported thesis format"',
        path,
    )
    text = remove_sequence_item(
        text,
        path,
        table="tasks.doc",
        item="test-filters",
    )
    text = remove_sequence_item(
        text,
        path,
        table="tasks.all",
        item="test-bootstrap",
    )
    text = remove_sequence_item(
        text,
        path,
        table="tasks.all",
        item="test-filters",
    )
    for task in ("bootstrap", "test-bootstrap", "test-filters"):
        text = remove_pixi_task(text, path, task)
    return text


def remove_template_files(root: Path) -> None:
    """Remove scripts and CI that exist only to validate the template.

    The ``scripts`` directory itself is kept, because ``scripts/install_tinytex.py``
    remains in use by the PDF tasks of a bootstrapped thesis. Its ``__init__.py`` is
    kept along with it, so that Ruff does not report an implicit namespace package.
    """
    template_files = (
        root / ".github" / "workflows" / "test-bootstrap.yml",
        root / "scripts" / "bootstrap.py",
        root / "scripts" / "check_bootstrap.py",
        root / "scripts" / "check_filters.py",
    )
    for path in template_files:
        path.unlink()
    shutil.rmtree(root / "scripts" / "__pycache__", ignore_errors=True)


def require_rub_answers(answers: Answers) -> RubAnswers:
    """Return the RUB-only values or fail if any of them is missing."""
    degree = answers.rub_degree
    faculty = answers.faculty
    first_examiner = answers.first_examiner
    second_examiner = answers.second_examiner
    if not (degree and faculty and first_examiner and second_examiner):
        message = "RUB configuration requires a degree, faculty, and two examiners"
        raise ValueError(message)
    return RubAnswers(degree, faculty, first_examiner, second_examiner)


def yaml_string(value: str, /) -> str:
    """Quote a string in a JSON form that is also valid YAML."""
    return json.dumps(value, ensure_ascii=False)


def replace_once(text: str, old: str, new: str, path: Path) -> str:
    """Replace one pristine-template placeholder or fail safely."""
    count = text.count(old)
    if count != 1:
        message = f"Expected one occurrence of {old!r} in {path}, found {count}. Has this repository already been bootstrapped?"
        raise RuntimeError(message)
    return text.replace(old, new)


class Profile(StrEnum):
    """Supported template profiles."""

    GENERAL = "general"
    RUB = "rub"


@dataclass(frozen=True)
class Answers:
    """Values used to replace template placeholders."""

    profile: Profile
    title: str
    subtitle: str
    given_name: str
    family_name: str
    institution: str
    department: str
    city: str
    country: str
    orcid: str
    date: str
    repository: str
    degree: str
    supervisor: str
    examiner: str
    defence_date: str
    rub_degree: str | None = None
    faculty: str | None = None
    first_examiner: str | None = None
    second_examiner: str | None = None


@dataclass(frozen=True)
class RubAnswers:
    """Values that only the RUB profile requires."""

    degree: str
    faculty: str
    first_examiner: str
    second_examiner: str


Validator = Callable[[str], str | None]


if __name__ == "__main__":
    typer.run(bootstrap)
