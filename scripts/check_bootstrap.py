"""Regression checks for the general and RUB bootstrap procedures."""

# cspell:ignore Boer Remco
# ruff: file-ignore[suspicious-subprocess-import, subprocess-without-shell-equals-true, start-process-with-partial-path]

from __future__ import annotations

import shutil
import subprocess
import tempfile
import tomllib
from pathlib import Path

PROFILES = ("general", "rub")
GIVEN_NAME = "Ada"
FAMILY_NAME = "Lovelace"
AUTHOR = f"{GIVEN_NAME} {FAMILY_NAME}"
TEMPLATE_AUTHOR = "Remco de Boer"


def main() -> None:
    """Bootstrap and validate both supported thesis profiles."""
    source = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="phd-thesis-bootstrap-") as temporary:
        temporary_root = Path(temporary)
        for profile in PROFILES:
            target = temporary_root / profile
            copy_repository(source, target)
            bootstrap(target, profile)
            validate_repository(target, profile)


def copy_repository(source: Path, target: Path) -> None:
    """Copy version-controlled repository files into an isolated directory."""
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        check=True,
        cwd=source,
        stdout=subprocess.PIPE,
    )
    for relative_bytes in result.stdout.split(b"\0"):
        if not relative_bytes:
            continue
        relative_path = Path(relative_bytes.decode())
        source_path = source / relative_path
        target_path = target / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)


def bootstrap(root: Path, profile: str) -> None:
    """Run the bootstrap command for one profile."""
    cache = root / "scripts" / "__pycache__"
    cache.mkdir()
    (cache / "bootstrap.cpython-313.pyc").touch()
    arguments = [
        "uv",
        "run",
        "scripts/bootstrap.py",
        "--profile",
        profile,
        "--title",
        "Example thesis",
        "--subtitle",
        "",
        "--given-name",
        GIVEN_NAME,
        "--family-name",
        FAMILY_NAME,
        "--institution",
        "Example University",
        "--department",
        "Physics",
        "--city",
        "Example City",
        "--country",
        "Example Country",
        "--orcid",
        "",
        "--date",
        "today",
        "--repository",
        "example/thesis",
        "--defence-date",
        "TBA",
    ]
    if profile == "rub":
        arguments.extend([
            "--rub-degree",
            "Doktors der Naturwissenschaften",
            "--faculty",
            "Fakultät für Physik und Astronomie",
            "--first-examiner",
            "First Examiner",
            "--second-examiner",
            "Second Examiner",
        ])
    else:
        arguments.extend([
            "--degree",
            "Doctor of Philosophy",
            "--supervisor",
            "Supervisor",
            "--examiner",
            "Examiner",
        ])
    subprocess.run(arguments, check=True, cwd=root)


def validate_repository(root: Path, profile: str) -> None:
    """Validate files, Pixi tasks, Quarto configuration, and HTML rendering."""
    for relative_path in (
        ".github/workflows/test-bootstrap.yml",
        "docs/_quarto-general.yml",
        "scripts/__pycache__",
        "scripts/bootstrap.py",
        "scripts/check_bootstrap.py",
        "scripts/check_filters.py",
    ):
        if (root / relative_path).exists():
            message = f"Bootstrap did not remove {relative_path} for {profile}"
            raise BootstrapRegressionError(message)
    for relative_path in ("scripts/__init__.py", "scripts/install_tinytex.py"):
        if not (root / relative_path).exists():
            message = f"Bootstrap removed {relative_path} for {profile}"
            raise BootstrapRegressionError(message)

    task_path = root / "pixi.toml"
    task_text = task_path.read_text(encoding="utf-8")
    tasks = tomllib.loads(task_text)["tasks"]
    assert_sequence(
        tasks["doc"]["depends-on"],
        ["html", "pdf", "epub", "paperback", "hardcover"],
        profile,
        task="doc",
    )
    assert_sequence(
        tasks["all"]["depends-on"],
        ["style", "linkcheck", "doc"],
        profile,
        task="all",
    )
    for task in (
        "bootstrap",
        "rub",
        "rub-hardcover",
        "rub-paperback",
        "test-bootstrap",
        "test-filters",
    ):
        if task in tasks:
            message = f"Template-only Pixi task {task!r} remains for {profile}"
            raise BootstrapRegressionError(message)
    expected_all = 'depends-on = [\n    "style",\n    "linkcheck",\n    "doc",\n]'
    if expected_all not in task_text:
        message = f"Pixi task dependencies were not preserved multiline for {profile}"
        raise BootstrapRegressionError(message)
    validate_license(root, profile)
    if profile == "general":
        validate_rub_removal(root)
    else:
        validate_general_removal(root)

    subprocess.run(
        ["uv", "run", "quarto", "inspect", "docs"],
        check=True,
        cwd=root,
        stdout=subprocess.DEVNULL,
    )
    subprocess.run(["uv", "run", "ruff", "check", "."], check=True, cwd=root)
    subprocess.run(["pixi", "run", "html"], check=True, cwd=root)


def validate_license(root: Path, profile: str) -> None:
    """Require the license to name the thesis author instead of the template author."""
    text = (root / "LICENSE").read_text(encoding="utf-8")
    if TEMPLATE_AUTHOR in text:
        message = (
            f"Template author {TEMPLATE_AUTHOR!r} remains in LICENSE for {profile}"
        )
        raise BootstrapRegressionError(message)
    if AUTHOR not in text:
        message = f"Author {AUTHOR!r} is missing from LICENSE for {profile}"
        raise BootstrapRegressionError(message)


def validate_rub_removal(root: Path) -> None:
    """Require the general profile to leave behind no RUB files or mentions."""
    for relative_path in ("docs/_quarto-rub.yml", "docs/themes"):
        if (root / relative_path).exists():
            message = f"Bootstrap did not remove {relative_path} for general"
            raise BootstrapRegressionError(message)
    for relative_path in (
        ".cspell.json",
        ".cspell/this-project.txt",
        "README.md",
        "docs/_quarto.yml",
        "docs/preamble/before-body.tex",
        "pixi.toml",
    ):
        text = (root / relative_path).read_text(encoding="utf-8").lower()
        for term in ("rub", "bochum"):
            if term in text:
                message = f"RUB mention {term!r} remains in {relative_path} for general"
                raise BootstrapRegressionError(message)
    hook_text = (root / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    if ".svg" in hook_text:
        message = "The RUB-only SVG pre-commit exclude remains for general"
        raise BootstrapRegressionError(message)


def validate_general_removal(root: Path) -> None:
    """Require the RUB profile to leave behind no general-profile configuration."""
    for relative_path, terms in (
        ("README.md", ("general", "supervisor")),
        ("docs/_quarto.yml", ("general", "supervisor", "rub-theme")),
        ("docs/preamble/before-body.tex", ("supervisor", "rub-theme", "$else$")),
    ):
        text = (root / relative_path).read_text(encoding="utf-8").lower()
        for term in terms:
            if term in text:
                message = f"General-profile leftover {term!r} remains in {relative_path} for rub"
                raise BootstrapRegressionError(message)


def assert_sequence(
    actual: list[str], expected: list[str], profile: str, *, task: str
) -> None:
    """Require a generated Pixi sequence to contain the expected items in order."""
    if actual != expected:
        message = (
            f"Unexpected {task!r} sequence for {profile}: "
            f"expected {expected!r}, found {actual!r}"
        )
        raise BootstrapRegressionError(message)


class BootstrapRegressionError(RuntimeError):
    """Indicate that a bootstrapped repository did not match expectations."""


if __name__ == "__main__":
    main()
