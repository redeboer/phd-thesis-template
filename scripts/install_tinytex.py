"""Install TinyTeX through Quarto, but only if no TeX distribution is available."""

# ruff: file-ignore[print, subprocess-without-shell-equals-true, suspicious-subprocess-import]

import shutil
import subprocess
import sys


def main() -> None:
    if has_tex_engine():
        print("A TeX engine is already available on PATH, skipping TinyTeX install")
        return
    if has_quarto_tinytex():
        print("Quarto already manages a TinyTeX installation, skipping install")
        return
    print("No TeX distribution found, installing TinyTeX through Quarto...")
    subprocess.check_call([
        *quarto(),
        "install",
        "tinytex",
        "--no-prompt",
        "--update-path",
    ])


def has_tex_engine() -> bool:
    return any(shutil.which(engine) for engine in ("xelatex", "pdflatex", "lualatex"))


def has_quarto_tinytex() -> bool:
    output = subprocess.check_output([*quarto(), "list", "tools"], text=True)
    for line in output.splitlines():
        if line.startswith("tinytex"):
            return "Not installed" not in line
    return False


def quarto() -> list[str]:
    executable = shutil.which("quarto")
    if executable is None:
        msg = "Could not find the quarto executable in the active environment"
        raise RuntimeError(msg)
    return [executable]


if __name__ == "__main__":
    sys.exit(main())
