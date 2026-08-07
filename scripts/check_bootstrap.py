"""Regression checks for the general and RUB bootstrap procedures."""

# ruff: file-ignore[suspicious-subprocess-import, subprocess-without-shell-equals-true, start-process-with-partial-path]

from __future__ import annotations

import shutil
import subprocess
import tempfile
import tomllib
from pathlib import Path

PROFILES = ("general", "rub")


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
        "Ada",
        "--family-name",
        "Lovelace",
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
        "scripts/__init__.py",
        "scripts/__pycache__",
        "scripts/bootstrap.py",
        "scripts/check_bootstrap.py",
        "scripts/check_filters.py",
    ):
        if (root / relative_path).exists():
            message = f"Bootstrap did not remove {relative_path} for {profile}"
            raise BootstrapRegressionError(message)
    if not (root / "scripts" / "install_tinytex.py").exists():
        message = f"Bootstrap removed scripts/install_tinytex.py for {profile}"
        raise BootstrapRegressionError(message)

    task_path = root / "pixi.toml"
    task_text = task_path.read_text(encoding="utf-8")
    tasks = tomllib.loads(task_text)["tasks"]
    actual_doc = tasks["doc"]["depends-on"]
    expected_doc = ["html", "pdf", "epub", "paperback", "hardcover"]
    if profile == "general":
        expected_doc.append("rub")
    assert_sequence(actual_doc, expected_doc, profile, task="doc")
    assert_sequence(
        tasks["all"]["depends-on"],
        ["style", "linkcheck", "doc"],
        profile,
        task="all",
    )
    for task in ("bootstrap", "test-bootstrap", "test-filters"):
        if task in tasks:
            message = f"Template-only Pixi task {task!r} remains for {profile}"
            raise BootstrapRegressionError(message)
    expected_all = 'depends-on = [\n    "style",\n    "linkcheck",\n    "doc",\n]'
    if expected_all not in task_text:
        message = f"Pixi task dependencies were not preserved multiline for {profile}"
        raise BootstrapRegressionError(message)

    subprocess.run(
        ["uv", "run", "quarto", "inspect", "docs"],
        check=True,
        cwd=root,
        stdout=subprocess.DEVNULL,
    )
    subprocess.run(["pixi", "run", "html"], check=True, cwd=root)


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
